"""
AES-256-GCM is used because it provides confidentiality and authenticity in one pass:
decryption verifies an authentication tag, so ciphertext tampering is detected
cryptographically. This property supports DPDP Act tamper-evidence expectations.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionError(Exception):
    pass


class DecryptionError(Exception):
    pass


class EncryptionService:
    def __init__(self, key_hex: str):
        if not isinstance(key_hex, str):
            raise ValueError("key_hex must be a string")
        if len(key_hex) != 64:
            raise ValueError("key_hex must be exactly 64 hex characters")
        try:
            key = bytes.fromhex(key_hex)
        except ValueError as exc:
            raise ValueError("key_hex must contain valid hexadecimal characters") from exc
        if len(key) != 32:
            raise ValueError("key_hex must decode to exactly 32 bytes")
        self._key = key

    def encrypt(self, plaintext: str) -> dict:
        if not isinstance(plaintext, str):
            raise EncryptionError("plaintext must be a string")
        try:
            nonce = os.urandom(12)
            ciphertext = AESGCM(self._key).encrypt(nonce, plaintext.encode("utf-8"), None)
            return {
                "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
                "nonce": base64.b64encode(nonce).decode("ascii"),
                "tag_included": True,
            }
        except Exception as exc:
            raise EncryptionError("AES-256-GCM encryption failed") from exc

    def decrypt(self, ciphertext_b64: str, nonce_b64: str) -> str:
        try:
            ciphertext = base64.b64decode(ciphertext_b64, validate=True)
            nonce = base64.b64decode(nonce_b64, validate=True)
        except Exception as exc:
            raise DecryptionError("invalid ciphertext or nonce encoding") from exc

        try:
            plaintext = AESGCM(self._key).decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except InvalidTag as exc:
            raise DecryptionError("ciphertext authentication failed") from exc
        except Exception as exc:
            raise DecryptionError("AES-256-GCM decryption failed") from exc

    def hash_for_audit(self, data: str) -> str:
        if not isinstance(data, str):
            raise EncryptionError("data must be a string")
        try:
            return hashlib.sha256(data.encode("utf-8")).hexdigest()
        except Exception as exc:
            raise EncryptionError("failed to compute SHA-256 hash") from exc

    def generate_session_key_hash(self, session_id: str) -> str:
        if not isinstance(session_id, str):
            raise EncryptionError("session_id must be a string")
        try:
            return hmac.new(
                self._key,
                session_id.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        except Exception as exc:
            raise EncryptionError("failed to generate session key hash") from exc

    def generate_consent_hash(self, session_id: str, timestamp: str) -> str:
        if not isinstance(session_id, str) or not isinstance(timestamp, str):
            raise EncryptionError("session_id and timestamp must be strings")
        try:
            payload = f"{session_id}{timestamp}DPDP_CONSENT_V1"
            return hashlib.sha256(payload.encode("utf-8")).hexdigest()
        except Exception as exc:
            raise EncryptionError("failed to generate consent hash") from exc

    def decrypt_owner_name(self, encrypted_json_str: str) -> str:
        """
        Decrypts owner_name from the JSON string stored in sessions.owner_name.

        The sessions table stores owner_name as:
        '{"ciphertext":"...","nonce":"...","tag_included":true}'
        """
        if not isinstance(encrypted_json_str, str) or not encrypted_json_str.strip():
            raise DecryptionError("owner_name payload must be a non-empty JSON string")
        try:
            payload = json.loads(encrypted_json_str)
            ciphertext = payload["ciphertext"]
            nonce = payload["nonce"]
        except Exception as exc:
            raise DecryptionError("owner_name payload is malformed") from exc
        return self.decrypt(ciphertext, nonce)

    def redact_for_demo(self, value: str, mode: str = "blur") -> str:
        """
        Produces a redacted representation of PII values for demo-mode surfaces.
        """
        value = "" if value is None else str(value)
        mode = (mode or "blur").lower().strip()
        if mode == "none":
            return value
        if mode == "partial":
            return f"{value[:2]}████" if value else "████████"
        return "████████"

    def verify_pdf_integrity(self, pdf_path: str, stored_hash: str) -> bool:
        """
        Recompute SHA-256 for a generated PDF and compare with stored hash.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(pdf_path)
        if not isinstance(stored_hash, str) or not stored_hash.strip():
            return False

        sha = hashlib.sha256()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha.update(chunk)
        return hmac.compare_digest(sha.hexdigest(), stored_hash.strip().lower())


def generate_dpdp_consent_receipt(
    session_id: str,
    owner_name_hash: str,
    timestamp: str,
    data_purposes: list[str],
) -> dict:
    """
    Generates a DPDP Act 2023 S.6 compliant consent receipt record.
    """
    receipt_id = str(uuid.uuid4())
    receipt_hash = hashlib.sha256(f"{receipt_id}{session_id}{timestamp}".encode("utf-8")).hexdigest()
    return {
        "receipt_id": receipt_id,
        "session_id": session_id,
        "timestamp": timestamp,
        "data_purposes": data_purposes or [],
        "legal_basis": "Digital Personal Data Protection Act 2023, Section 6",
        "consent_scope": "Financial data analysis for credit assessment",
        "retention_period": "7 years per RBI record-keeping guidelines",
        "right_to_erasure": f"POST /api/v1/sessions/{session_id} DELETE",
        "owner_identity_hash": owner_name_hash,
        "receipt_hash": receipt_hash,
    }
