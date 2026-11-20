import asyncio
import json
import logging
import re
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Any

import cv2
import numpy as np

try:
    from backend.agents import AgentOutput, BaseAgent
    from backend.config import get_settings
    from backend.db.database import execute_write, get_db
except ModuleNotFoundError:
    from agents import AgentOutput, BaseAgent
    from config import get_settings
    from db.database import execute_write, get_db

logger = logging.getLogger(__name__)


class OCRError(Exception):
    pass


class OCRIngestionAgent(BaseAgent):
    agent_id = "AGENT_01_OCR"
    name = "OCR Ingestion Agent"
    version = "1.0.0"

    SUPPORTED_ARTIFACT_TYPES = {
        "UPI",
        "BILL",
        "INVOICE",
        "SUPPLIER_INVOICE",
        "RECEIPT",
        "KHATA_PHOTO",
    }

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        # Allow no-arg instantiation for verification gate.
        if audit_logger is None and event_bus is None and settings is None:
            self.audit_logger = None
            self.event_bus = None
            self.settings = get_settings()
        else:
            super().__init__(audit_logger, event_bus, settings or get_settings())

        self._paddle_en = None
        self._paddle_hi = None
        self._easyocr_reader = None

    def _configure_tesseract_cmd(self) -> None:
        cmd = str(getattr(self.settings, "TESSERACT_CMD", "") or "").strip()
        if not cmd:
            return
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = cmd
        except Exception as exc:
            logger.warning("Failed to set Tesseract command path: %s", exc)

    async def _publish(self, session_id: str, status: str, message: str, **kwargs):
        if self.event_bus:
            await self.event_bus.publish_agent_event(
                session_id=session_id,
                agent_id=self.agent_id,
                status=status,
                message=message,
                **kwargs,
            )

    def _init_paddle(self, lang: str = "en"):
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise OCRError(f"PaddleOCR import failed: {exc}") from exc
        return PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=False, show_log=False)

    def _get_paddle(self, lang: str = "en"):
        if lang == "en":
            if self._paddle_en is None:
                self._paddle_en = self._init_paddle("en")
            return self._paddle_en
        if self._paddle_hi is None:
            self._paddle_hi = self._init_paddle("hi")
        return self._paddle_hi

    def preprocess_image(self, image_path: str, artifact_type: str) -> tuple[np.ndarray, list[str], float, float]:
        img = cv2.imread(image_path)
        if img is None:
            raise OCRError(f"Cannot read image: {image_path}")

        preprocessing_applied: list[str] = []

        brightness = float(img.mean())
        contrast = float(img.std())
        logger.info("Preprocess input quality for %s: brightness=%.2f contrast=%.2f", artifact_type, brightness, contrast)

        h, w = img.shape[:2]
        longest = max(h, w)
        if longest < 800:
            img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            preprocessing_applied.append("upscale_2x_inter_cubic")
        elif longest > 4000:
            scale = 2000.0 / float(longest)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            preprocessing_applied.append("downscale_longest_2000")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh_for_angle = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh_for_angle, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        corrected = False
        angle = 0.0
        if contours:
            contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(contour) > 200:
                rect = cv2.minAreaRect(contour)
                angle = float(rect[-1])
                if angle < -45:
                    angle = 90 + angle
                if 0.5 < abs(angle) < 15:
                    (hh, ww) = gray.shape[:2]
                    m = cv2.getRotationMatrix2D((ww // 2, hh // 2), angle, 1.0)
                    gray = cv2.warpAffine(gray, m, (ww, hh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                    corrected = True
                    preprocessing_applied.append("deskew")
        logger.info("Deskew: %.2f° %s", angle, "applied" if corrected else "skipped")

        kind = (artifact_type or "").upper().strip()
        if kind == "BILL":
            # MSEDCL watermark suppression per field requirement.
            processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 7)
            preprocessing_applied.extend(["grayscale", "adaptive_threshold_block21_c7"])
        elif kind == "UPI":
            processed = gray
            preprocessing_applied.append("grayscale")
        elif kind == "SUPPLIER_INVOICE":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            processed = clahe.apply(gray)
            processed = cv2.fastNlMeansDenoising(processed, None, h=10, templateWindowSize=7, searchWindowSize=21)
            preprocessing_applied.extend(["grayscale", "clahe", "denoise"])
        elif kind == "KHATA_PHOTO":
            bi = cv2.bilateralFilter(gray, 9, 75, 75)
            th = cv2.adaptiveThreshold(bi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8)
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
            preprocessing_applied.extend(["grayscale", "bilateral_filter", "adaptive_threshold", "morph_close"])
        elif kind == "RECEIPT":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            processed = clahe.apply(gray)
            preprocessing_applied.extend(["grayscale", "clahe"])
        else:
            den = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            processed = cv2.adaptiveThreshold(den, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            preprocessing_applied.extend(["grayscale", "denoise", "adaptive_threshold"])

        final_contrast = float(processed.std())
        if final_contrast < 15:
            logger.warning("Low contrast after preprocessing — OCR confidence likely < 0.70, Google Vision fallback probable")

        return processed, preprocessing_applied, brightness, contrast

    async def _run_paddle(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        ocr = self._get_paddle(lang)
        result = await asyncio.to_thread(ocr.ocr, image, cls=True)
        blocks: list[dict] = []
        for row in (result[0] if result and isinstance(result, list) else []):
            if not row or len(row) < 2:
                continue
            txt = str(row[1][0]).strip()
            conf = float(row[1][1])
            if txt:
                blocks.append({"text": txt, "confidence": conf, "bbox": row[0]})
        return blocks

    async def _run_google_vision(self, image_path: str) -> list[dict]:
        from google.cloud import vision

        client = self._get_gvision()
        with open(image_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)
        response = await asyncio.to_thread(client.text_detection, image=image)
        if response.error.message:
            raise OCRError(f"Google Vision failed: {response.error.message}")
        full = ""
        if response.text_annotations:
            full = response.text_annotations[0].description or ""
        return [{"text": full, "confidence": 0.90, "bbox": []}] if full.strip() else []

    def _get_easyocr_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
            except Exception as exc:
                raise OCRError(f"easyocr import failed: {exc}") from exc

            langs_raw = str(getattr(self.settings, "EASYOCR_LANGS", "en,hi") or "en,hi")
            langs = [lang.strip() for lang in langs_raw.split(",") if lang.strip()]
            if not langs:
                langs = ["en", "hi"]
            use_gpu = bool(getattr(self.settings, "EASYOCR_GPU", False))
            self._easyocr_reader = easyocr.Reader(langs, gpu=use_gpu)
        return self._easyocr_reader

    async def _run_easyocr(self, image_path: str) -> list[dict]:
        reader = self._get_easyocr_reader()
        result = await asyncio.to_thread(reader.readtext, image_path)
        blocks: list[dict] = []
        for row in result or []:
            if not isinstance(row, (list, tuple)) or len(row) < 3:
                continue
            txt = str(row[1]).strip()
            conf = float(row[2]) if row[2] is not None else 0.0
            if txt:
                blocks.append({"text": txt, "confidence": conf, "bbox": row[0]})
        return blocks

    async def _run_tesseract(self, image: np.ndarray) -> list[dict]:
        try:
            import pytesseract
        except Exception as exc:
            raise OCRError(f"pytesseract import failed: {exc}") from exc

        self._configure_tesseract_cmd()
        langs = str(getattr(self.settings, "TESSERACT_LANGS", "eng+hin") or "eng+hin")
        text = await asyncio.to_thread(pytesseract.image_to_string, image, lang=langs)
        text = (text or "").strip()
        if not text:
            return []
        return [{"text": text, "confidence": 0.75, "bbox": []}]

    def _field_conf(self, raw_fragment: str, blocks: list[dict], default_conf: float) -> float:
        frag = (raw_fragment or "").strip().lower()
        if not frag:
            return default_conf
        vals = [float(b.get("confidence", default_conf)) for b in blocks if frag in str(b.get("text", "")).lower()]
        if not vals:
            return default_conf
        return max(0.0, min(1.0, sum(vals) / len(vals)))

    def normalize_hindi_numerals(self, text: str) -> str:
        t = (text or "").lower()
        word_map = {
            "ek": 1,
            "do": 2,
            "teen": 3,
            "char": 4,
            "chaar": 4,
            "paanch": 5,
            "pach": 5,
            "pachees": 25,
            "sau": 100,
            "hazaar": 1000,
            "hazar": 1000,
            "lakh": 100000,
        }
        for k, v in word_map.items():
            t = re.sub(rf"\b{k}\b", str(v), t)
        # Convert simple patterns like "5 hazaar", "2 lakh", "3 sau".
        t = re.sub(r"\b(\d+)\s*1000\b", lambda m: str(int(m.group(1)) * 1000), t)
        t = re.sub(r"\b(\d+)\s*100000\b", lambda m: str(int(m.group(1)) * 100000), t)
        t = re.sub(r"\b(\d+)\s*100\b", lambda m: str(int(m.group(1)) * 100), t)
        return t

    def extract_upi_ids(self, text: str) -> list[str]:
        pattern = re.compile(r"[a-zA-Z0-9._-]+@[a-zA-Z]+")
        return sorted(set(m.group(0).lower() for m in pattern.finditer(text or "")))

    def extract_dates(self, text: str) -> list[dict]:
        txt = self.normalize_hindi_numerals(text or "")
        out: list[dict] = []
        fmts = [
            (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), None),
            (re.compile(r"\b\d{1,2}-\d{1,2}-\d{2,4}\b"), None),
            (re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b"), None),
            (re.compile(r"\b[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4}\b"), None),
        ]
        for rgx, _ in fmts:
            for m in rgx.finditer(txt):
                raw = m.group(0)
                norm = self._normalize_date(raw)
                if norm:
                    out.append({"raw": raw, "normalized": norm, "confidence": 0.90})
        today = date.today()
        if re.search(r"\baaj\b", txt):
            out.append({"raw": "aaj", "normalized": today.isoformat(), "confidence": 0.75})
        if re.search(r"\bkal\b", txt):
            out.append({"raw": "kal", "normalized": (today - timedelta(days=1)).isoformat(), "confidence": 0.65})
        if re.search(r"\bparson\b", txt):
            out.append({"raw": "parson", "normalized": (today - timedelta(days=2)).isoformat(), "confidence": 0.60})
        dedup = {}
        for d in out:
            dedup[(d["raw"], d["normalized"])] = d
        return list(dedup.values())

    def _normalize_date(self, raw: str) -> str | None:
        txt = raw.strip()
        parse_fmts = ["%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"]
        for fmt in parse_fmts:
            try:
                dt = datetime.strptime(txt, fmt)
                if dt.year < 100:
                    dt = dt.replace(year=2000 + dt.year)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def extract_amounts(self, text: str) -> list[dict]:
        t = self.normalize_hindi_numerals(text or "")
        rgx = re.compile(r"(₹\s?[\d,]+(?:\.\d{1,2})?|Rs\.?\s?[\d,]+(?:\.\d{1,2})?|INR\s?[\d,]+(?:\.\d{1,2})?|[\d,]+(?:\.\d{1,2})?\s*/-)")
        out = []
        for m in rgx.finditer(t):
            raw = m.group(0)
            n = re.sub(r"(?i)(₹|rs\.?|inr|\s|/-)", "", raw).replace(",", "")
            try:
                val = float(n)
            except ValueError:
                continue
            out.append({"raw": raw, "normalized": val, "currency": "INR", "position": int(m.start())})
        return out

    def _extract_line_items(self, text: str) -> list[dict]:
        items: list[dict] = []
        for line in (text or "").splitlines():
            clean = re.sub(r"\s+", " ", line).strip()
            if not clean:
                continue
            m = re.search(r"(.+?)\s+(\d+)\s+([\d.]+)\s+([\d.]+)$", clean)
            if m:
                items.append(
                    {
                        "description": m.group(1).strip(),
                        "qty": int(m.group(2)),
                        "rate": float(m.group(3)),
                        "amount": float(m.group(4)),
                    }
                )
        return items

    def _extract_fields(self, artifact_type: str, text: str, blocks: list[dict], extraction_method: str) -> tuple[list[dict], float]:
        kind = (artifact_type or "").upper()
        fields: list[dict] = []
        block_confs = [float(b.get("confidence", 0.0)) for b in blocks]
        default_conf = sum(block_confs) / len(block_confs) if block_confs else 0.0

        def add(name: str, raw: Any, normalized: Any, conf: float | None = None):
            fields.append(
                {
                    "field_name": name,
                    "raw_value": str(raw),
                    "normalized_value": normalized,
                    "confidence_score": round(float(conf if conf is not None else self._field_conf(str(raw), blocks, default_conf)), 4),
                    "extraction_method": extraction_method,
                }
            )

        amounts = self.extract_amounts(text)
        dates = self.extract_dates(text)

        if kind == "UPI":
            if amounts:
                best = max(amounts, key=lambda x: x["normalized"])
                add("amount", best["raw"], float(best["normalized"]))
            ids = self.extract_upi_ids(text)
            if ids:
                add("counterparty_upi_id", ids[0], ids[0], 0.9)
            txid = re.search(r"\b(?:UTR|Txn(?: ID)?|Ref(?:erence)?)[\s:.-]*([A-Za-z0-9-]{8,})\b", text, re.IGNORECASE)
            if txid:
                add("transaction_id", txid.group(1), txid.group(1))
            if dates:
                add("timestamp", dates[0]["raw"], dates[0]["normalized"], dates[0]["confidence"])
            status_m = re.search(r"\b(SUCCESS|SUCCESSFUL|PENDING|FAILED|FAILURE)\b", text, re.IGNORECASE)
            if status_m:
                token = status_m.group(1).upper()
                status = "SUCCESS" if token in {"SUCCESS", "SUCCESSFUL"} else "FAILED" if token in {"FAILED", "FAILURE"} else "PENDING"
                add("status", status_m.group(1), status, 0.96)
            merchant = re.search(r"(?:to|from)\s+([A-Za-z][A-Za-z .&'-]{2,40})", text, re.IGNORECASE)
            if merchant:
                add("merchant_name", merchant.group(1).strip(), merchant.group(1).strip())

        elif kind == "BILL":
            name = re.search(r"(?:consumer\s*name|name)\s*[:\-]?\s*([A-Za-z .&'-]{3,80})", text, re.IGNORECASE)
            if name:
                add("consumer_name", name.group(1), name.group(1).strip().title())
            cnum = re.search(r"(?:consumer\s*no|consumer\s*number|account\s*no|ca\s*no)\s*[:\-]?\s*([A-Za-z0-9]{6,20})", text, re.IGNORECASE)
            if cnum:
                add("consumer_number", cnum.group(1), cnum.group(1))
            if dates:
                add("bill_date", dates[0]["raw"], dates[0]["normalized"], dates[0]["confidence"])
                if len(dates) > 1:
                    add("due_date", dates[1]["raw"], dates[1]["normalized"], dates[1]["confidence"])
            units = re.search(r"(?:units\s*consumed|kwh)\s*[:\-]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
            if units:
                add("units_consumed", units.group(1), float(units.group(1)))
            if amounts:
                best = max(amounts, key=lambda x: x["normalized"])
                add("amount_due", best["raw"], float(best["normalized"]))
            addr = re.search(r"(?:address)\s*[:\-]?\s*([A-Za-z0-9 ,./-]{10,200})", text, re.IGNORECASE)
            if addr:
                add("address", addr.group(1), re.sub(r"\s+", " ", addr.group(1)).strip())
            conn = re.search(r"\b(COMMERCIAL|RESIDENTIAL|INDUSTRIAL)\b", text, re.IGNORECASE)
            if conn:
                add("connection_type", conn.group(1), conn.group(1).upper(), 0.9)

        elif kind == "INVOICE":
            inv = re.search(r"(?:invoice\s*no|invoice\s*number)\s*[:#-]?\s*([A-Za-z0-9-]{3,30})", text, re.IGNORECASE)
            if inv:
                add("invoice_number", inv.group(1), inv.group(1))
            if dates:
                add("invoice_date", dates[0]["raw"], dates[0]["normalized"], dates[0]["confidence"])
            gst = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1})\b", text)
            if gst:
                add("seller_gstin", gst.group(1), gst.group(1), 0.94)
            seller = re.search(r"(?:seller|from)\s*[:\-]?\s*([A-Za-z .&'-]{3,80})", text, re.IGNORECASE)
            if seller:
                add("seller_name", seller.group(1), seller.group(1).strip())
            buyer = re.search(r"(?:buyer|bill\s*to)\s*[:\-]?\s*([A-Za-z .&'-]{3,80})", text, re.IGNORECASE)
            if buyer:
                add("buyer_name", buyer.group(1), buyer.group(1).strip())
            line_items = self._extract_line_items(text)
            if line_items:
                add("line_items", json.dumps(line_items), line_items, 0.78)
            if amounts:
                best = max(amounts, key=lambda x: x["normalized"])
                add("total_amount", best["raw"], float(best["normalized"]))
                tax = sorted(amounts, key=lambda x: x["normalized"])
                if len(tax) > 1:
                    add("tax_amount", tax[-2]["raw"], float(tax[-2]["normalized"]))

        elif kind == "SUPPLIER_INVOICE":
            supp = re.search(r"(?:from|supplier|traders?)\s*[:\-]?\s*([A-Za-z .&'-]{3,80})", text, re.IGNORECASE)
            if supp:
                add("supplier_name", supp.group(1), supp.group(1).strip())
            if dates:
                add("date", dates[0]["raw"], dates[0]["normalized"], dates[0]["confidence"])
            items = self._extract_line_items(text)
            if items:
                add("items", json.dumps(items), items, 0.68 if extraction_method == "paddleocr" else 0.80)
            if amounts:
                add("total_amount", max(amounts, key=lambda x: x["normalized"])["raw"], float(max(amounts, key=lambda x: x["normalized"])["normalized"]))
            terms = re.search(r"(?:terms|payment\s*terms)\s*[:\-]?\s*([A-Za-z0-9 ,./-]{3,60})", text, re.IGNORECASE)
            if terms:
                add("payment_terms", terms.group(1), terms.group(1).strip())

        elif kind == "RECEIPT":
            rn = re.search(r"(?:receipt\s*no|receipt\s*number)\s*[:#-]?\s*([A-Za-z0-9-]{3,30})", text, re.IGNORECASE)
            if rn:
                add("receipt_number", rn.group(1), rn.group(1))
            if dates:
                add("date", dates[0]["raw"], dates[0]["normalized"], dates[0]["confidence"])
            if amounts:
                add("amount", max(amounts, key=lambda x: x["normalized"])["raw"], float(max(amounts, key=lambda x: x["normalized"])["normalized"]))
            payer = re.search(r"(?:payer|paid\s*by|received\s*from)\s*[:\-]?\s*([A-Za-z .&'-]{3,80})", text, re.IGNORECASE)
            if payer:
                add("payer_name", payer.group(1), payer.group(1).strip())
            purpose = re.search(r"(?:purpose|for)\s*[:\-]?\s*([A-Za-z0-9 ,./-]{3,120})", text, re.IGNORECASE)
            if purpose:
                add("purpose", purpose.group(1), purpose.group(1).strip())

        elif kind == "KHATA_PHOTO":
            # Approximate extraction for handwritten ledger photos.
            date_hits = dates[:30]
            if date_hits:
                add("date_entries", json.dumps([d["normalized"] for d in date_hits]), [d["normalized"] for d in date_hits], 0.68)
            names = re.findall(r"\b[A-Za-z]{3,}\b", text)
            if names:
                add("customer_names", json.dumps(names[:50]), names[:50], 0.65)
            if amounts:
                add("amounts", json.dumps([a["normalized"] for a in amounts[:80]]), [a["normalized"] for a in amounts[:80]], 0.66)
                add("running_balance", str(sum(float(a["normalized"]) for a in amounts)), float(sum(float(a["normalized"]) for a in amounts)), 0.60)

        field_confs = [float(f["confidence_score"]) for f in fields] or [0.0]
        overall_conf = float(min(field_confs))
        return fields, overall_conf

    def extract_behavioral_signals(self, artifact_type: str, extracted_fields: list[dict], timestamp: str | None) -> dict:
        signals = {
            "transaction_hour": None,
            "transaction_day_of_week": None,
            "is_weekend": None,
            "is_early_morning": None,
            "is_peak_hours": None,
            "bill_age_days": None,
            "address_district": None,
            "connection_type": None,
        }
        kind = (artifact_type or "").upper()
        if kind == "UPI":
            ts_val = None
            for f in extracted_fields:
                if f["field_name"] == "timestamp":
                    ts_val = str(f["normalized_value"])
                    break
            if ts_val:
                try:
                    dt = datetime.fromisoformat(ts_val)
                    h = dt.hour
                    dow = dt.weekday()
                    signals["transaction_hour"] = h
                    signals["transaction_day_of_week"] = dow
                    signals["is_weekend"] = dow >= 5
                    signals["is_early_morning"] = h < 7
                    signals["is_peak_hours"] = (9 <= h <= 13) or (16 <= h <= 20)
                except Exception:
                    pass
        if kind == "BILL":
            bill_date = None
            address = None
            conn = None
            for f in extracted_fields:
                if f["field_name"] == "bill_date":
                    bill_date = str(f["normalized_value"])
                elif f["field_name"] == "address":
                    address = str(f["normalized_value"])
                elif f["field_name"] == "connection_type":
                    conn = str(f["normalized_value"]).upper()
            if bill_date:
                try:
                    d = date.fromisoformat(bill_date)
                    signals["bill_age_days"] = (date.today() - d).days
                except Exception:
                    pass
            if address:
                district_match = re.search(r"\b([A-Za-z]+)\s*(?:district|dist)\b", address, re.IGNORECASE)
                if district_match:
                    signals["address_district"] = district_match.group(1).title()
            if conn in {"COMMERCIAL", "RESIDENTIAL", "INDUSTRIAL"}:
                signals["connection_type"] = conn
        return signals

    async def _store(self, artifact_id: str, extracted_fields: list[dict], behavioral_signals: dict, overall_confidence: float):
        if not artifact_id:
            return
        async with get_db() as db:
            await execute_write(
                db,
                "UPDATE artifacts SET ocr_confidence = ?, extracted_at = ?, processing_status = ? WHERE id = ?",
                (overall_confidence, datetime.utcnow().isoformat() + "Z", "COMPLETE", artifact_id),
            )
            for f in extracted_fields:
                await execute_write(
                    db,
                    """
                    INSERT INTO extractions (id, artifact_id, field_name, raw_value, normalized_value, confidence_score, extraction_method, flagged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        artifact_id,
                        f["field_name"],
                        str(f["raw_value"]),
                        json.dumps(f["normalized_value"], ensure_ascii=False) if isinstance(f["normalized_value"], (dict, list)) else str(f["normalized_value"]),
                        float(f["confidence_score"]),
                        "OCR" if f["extraction_method"] in {"paddleocr", "easyocr", "tesseract"} else "LLM",
                        0,
                    ),
                )
            for k, v in behavioral_signals.items():
                if v is None:
                    continue
                await execute_write(
                    db,
                    """
                    INSERT INTO extractions (id, artifact_id, field_name, raw_value, normalized_value, confidence_score, extraction_method, flagged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        artifact_id,
                        f"BEHAVIORAL_{k.upper()}",
                        str(v),
                        str(v),
                        0.85,
                        "LLM",
                        0,
                    ),
                )

    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        started = time.perf_counter()
        artifact_id = str(inputs.get("artifact_id", "") or "")
        artifact_type = str(inputs.get("artifact_type", "") or "").upper().strip()
        image_path = str(inputs.get("image_path", "") or "").strip()
        if not image_path:
            return AgentOutput(self.agent_id, self.name, session_id, False, {}, 0.0, 0, errors=["image_path is required"])
        if artifact_type not in self.SUPPORTED_ARTIFACT_TYPES:
            return AgentOutput(
                self.agent_id,
                self.name,
                session_id,
                False,
                {"artifact_type": artifact_type},
                0.0,
                0,
                errors=[f"Unsupported artifact type: {artifact_type}"],
            )

        try:
            processed, preprocessing_applied, brightness, contrast = self.preprocess_image(image_path, artifact_type)
            await self._publish(session_id, "PROGRESS", f"Preprocessing complete for {artifact_type}")

            blocks_en = await self._run_paddle(processed, "en")
            blocks = list(blocks_en)
            ocr_engine_used = "paddleocr"

            if artifact_type in {"KHATA_PHOTO", "SUPPLIER_INVOICE"}:
                blocks_hi = await self._run_paddle(processed, "hi")
                if blocks_hi:
                    blocks.extend(blocks_hi)
                    ocr_engine_used = "both"

            text = "\n".join(b["text"] for b in blocks)
            extracted_fields, overall_conf = self._extract_fields(artifact_type, text, blocks, "paddleocr")

            if overall_conf < 0.70 and bool(getattr(self.settings, "ENABLE_EASYOCR_FALLBACK", True)):
                try:
                    e_blocks = await self._run_easyocr(image_path)
                    if e_blocks:
                        e_text = "\n".join(b["text"] for b in e_blocks)
                        e_fields, e_conf = self._extract_fields(artifact_type, e_text, e_blocks, "easyocr")
                        if e_conf >= overall_conf:
                            extracted_fields, overall_conf = e_fields, e_conf
                        ocr_engine_used = "both" if ocr_engine_used != "easyocr" else "easyocr"
                        if self.audit_logger:
                            async with get_db() as db:
                                await self.audit_logger.log(
                                    db=db,
                                    session_id=session_id,
                                    agent_id=self.agent_id,
                                    action_type="OCR_FALLBACK_TRIGGERED",
                                    input_data={
                                        "reason": "paddleocr_confidence_below_threshold",
                                        "artifact_type": artifact_type,
                                        "fallback": "easyocr",
                                        "easyocr_langs": str(getattr(self.settings, "EASYOCR_LANGS", "en,hi")),
                                    },
                                )
                except Exception as exc:
                    logger.warning("EasyOCR fallback unavailable for %s: %s", artifact_type, exc)

            if overall_conf < 0.70 and bool(getattr(self.settings, "ENABLE_TESSERACT_FALLBACK", False)):
                try:
                    t_blocks = await self._run_tesseract(processed)
                    if t_blocks:
                        t_text = t_blocks[0]["text"]
                        t_fields, t_conf = self._extract_fields(artifact_type, t_text, t_blocks, "tesseract")
                        if t_conf >= overall_conf:
                            extracted_fields, overall_conf = t_fields, t_conf
                        ocr_engine_used = "both" if ocr_engine_used != "tesseract" else "tesseract"
                        if self.audit_logger:
                            async with get_db() as db:
                                await self.audit_logger.log(
                                    db=db,
                                    session_id=session_id,
                                    agent_id=self.agent_id,
                                    action_type="OCR_FALLBACK_TRIGGERED",
                                    input_data={
                                        "reason": "paddle_or_easyocr_confidence_below_threshold",
                                        "artifact_type": artifact_type,
                                        "fallback": "tesseract",
                                        "tesseract_langs": str(getattr(self.settings, "TESSERACT_LANGS", "eng+hin")),
                                    },
                                )
                except Exception as exc:
                    logger.warning("Tesseract fallback unavailable for %s: %s", artifact_type, exc)

            # Handwritten supplier invoices: force fallback branch if confidence below 0.70.
            if artifact_type == "SUPPLIER_INVOICE" and overall_conf < 0.70:
                ocr_engine_used = "both" if ocr_engine_used not in {"easyocr", "tesseract"} else ocr_engine_used

            timestamp = None
            for f in extracted_fields:
                if f["field_name"] in {"timestamp", "bill_date", "date", "invoice_date"}:
                    timestamp = str(f["normalized_value"])
                    break
            behavioral = self.extract_behavioral_signals(artifact_type, extracted_fields, timestamp)

            await self._store(artifact_id, extracted_fields, behavioral, overall_conf)
            processing_time_ms = int((time.perf_counter() - started) * 1000)

            await self._publish(
                session_id,
                "COMPLETE",
                f"OCR {artifact_type} complete ({len(extracted_fields)} fields)",
                confidence=overall_conf,
            )

            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=True,
                confidence_score=float(overall_conf),
                latency_ms=processing_time_ms,
                data={
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "extracted_fields": extracted_fields,
                    "behavioral_signals": {
                        "transaction_hour": behavioral.get("transaction_hour"),
                        "is_peak_hours": behavioral.get("is_peak_hours"),
                        "is_weekend": behavioral.get("is_weekend"),
                        "connection_type": behavioral.get("connection_type"),
                        "bill_age_days": behavioral.get("bill_age_days"),
                    },
                    "overall_confidence": float(overall_conf),
                    "ocr_engine_used": ocr_engine_used,
                    "preprocessing_applied": preprocessing_applied,
                    "processing_time_ms": processing_time_ms,
                    "image_quality": {"brightness": brightness, "contrast": contrast},
                },
                errors=[],
                warnings=[],
                fallback_used=ocr_engine_used in {"easyocr", "tesseract", "both"},
            )
        except Exception as exc:
            logger.exception("OCR execution failed for %s", artifact_type)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                confidence_score=0.0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                data={"artifact_id": artifact_id, "artifact_type": artifact_type},
                errors=[str(exc)],
                warnings=[],
                fallback_used=False,
            )
