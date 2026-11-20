import math
from difflib import SequenceMatcher
from pathlib import Path
import importlib.util

import httpx


def _load_backend_agents():
    try:
        from backend.agents import AgentOutput, BaseAgent  # type: ignore

        return AgentOutput, BaseAgent
    except Exception:
        backend_agents_path = Path(__file__).resolve().parents[1] / "backend" / "agents" / "__init__.py"
        spec = importlib.util.spec_from_file_location("shadow_backend_agents", str(backend_agents_path))
        if spec is None or spec.loader is None:
            raise ImportError("Unable to load backend.agents BaseAgent/AgentOutput")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.AgentOutput, module.BaseAgent


AgentOutput, BaseAgent = _load_backend_agents()


class MapsVerificationError(Exception):
    pass


class GoogleMapsVerificationAgent(BaseAgent):
    agent_id = "AGENT_00_MAPS"
    name = "Google Maps Verification Agent"
    version = "1.0.0"

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        if audit_logger is None and event_bus is None and settings is None:
            self.audit_logger = None
            self.event_bus = None
            self.settings = None
        else:
            super().__init__(audit_logger, event_bus, settings)

    async def _audit_mock_data(self, session_id: str, business_name: str, address: str, pin_code: str):
        if not self.audit_logger:
            return
        try:
            await self.audit_logger.log(
                db=None,
                session_id=session_id,
                event_type="GOOGLE_MAPS_MOCK_DATA_USED",
                agent_id=self.agent_id,
                details={
                    "business_name": business_name,
                    "address": address,
                    "pin_code": pin_code,
                },
            )
        except Exception:
            return

    @staticmethod
    def _mock_result() -> dict:
        return {
            "place_found": True,
            "place_name": "Suresh Kirana Store",
            "name_match_score": 0.89,
            "rating": 4.2,
            "review_count": 47,
            "is_permanently_closed": False,
            "is_operational": True,
            "address_match": True,
            "place_url": "https://maps.google.com/?q=Suresh+Kirana+Store",
            "photo_reference": None,
            "maps_confidence": 0.85,
            "continuity_from_maps": 0.76,
            "mock_data": True,
        }

    async def verify_business_on_maps(self, business_name: str, address: str, pin_code: str) -> dict:
        provider = str(getattr(self.settings, "MAPS_PROVIDER", "mock") or "mock").strip().lower() if self.settings else "mock"
        if provider in {"osm", "nominatim"}:
            return await self._verify_business_on_osm(business_name, address, pin_code)
        if provider == "auto" and not getattr(self.settings, "GOOGLE_MAPS_API_KEY", None):
            return await self._verify_business_on_osm(business_name, address, pin_code)

        api_key = getattr(self.settings, "GOOGLE_MAPS_API_KEY", None) if self.settings else None
        if not api_key:
            return self._mock_result()

        query = f"{business_name} {address} {pin_code}".strip()
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        detail_url = "https://maps.googleapis.com/maps/api/place/details/json"

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                search_resp = await client.get(search_url, params={"query": query, "key": api_key})
                search_resp.raise_for_status()
                search_json = search_resp.json()
            except Exception as exc:
                raise MapsVerificationError(f"Google Text Search failed: {exc}") from exc

            results = search_json.get("results") or []
            if not results:
                return {
                    "place_found": False,
                    "place_name": "",
                    "name_match_score": 0.0,
                    "rating": 0.0,
                    "review_count": 0,
                    "is_permanently_closed": False,
                    "is_operational": False,
                    "address_match": False,
                    "place_url": "",
                    "photo_reference": None,
                    "maps_confidence": 0.0,
                    "continuity_from_maps": 0.0,
                    "mock_data": False,
                }

            place_id = str(results[0].get("place_id") or "")
            if not place_id:
                raise MapsVerificationError("Google Text Search returned no place_id")

            fields = "name,formatted_address,rating,user_ratings_total,opening_hours,business_status,photos,types,url"
            try:
                detail_resp = await client.get(detail_url, params={"place_id": place_id, "fields": fields, "key": api_key})
                detail_resp.raise_for_status()
                details_json = detail_resp.json()
            except Exception as exc:
                raise MapsVerificationError(f"Google Place Details failed: {exc}") from exc

        details = details_json.get("result") or {}
        place_name = str(details.get("name") or "")
        formatted_address = str(details.get("formatted_address") or "")
        rating = float(details.get("rating") or 0.0)
        review_count = int(details.get("user_ratings_total") or 0)
        business_status = str(details.get("business_status") or "")
        is_operational = business_status.upper() == "OPERATIONAL"
        is_permanently_closed = business_status.upper() == "CLOSED_PERMANENTLY"
        address_match = str(pin_code or "").strip() in formatted_address
        place_url = str(details.get("url") or "")
        photos = details.get("photos") or []
        photo_reference = photos[0].get("photo_reference") if photos else None

        name_match_score = SequenceMatcher(None, business_name.lower().strip(), place_name.lower().strip()).ratio()

        base = 0.0
        if place_name:
            base += 0.40
        if name_match_score > 0.70:
            base += 0.20
        if review_count >= 10:
            base += 0.15
        if review_count >= 50:
            base += 0.10
        if is_operational:
            base += 0.10
        if address_match:
            base += 0.05
        maps_confidence = min(base, 1.0)

        review_score = min(math.log10(review_count + 1) / math.log10(200), 1.0) if review_count >= 0 else 0.0
        rating_score = (rating - 1.0) / 4.0 if rating > 0 else 0.5
        continuity_from_maps = (review_score * 0.6) + (rating_score * 0.4)
        continuity_from_maps = max(0.0, min(1.0, continuity_from_maps))

        return {
            "place_found": bool(place_name),
            "place_name": place_name,
            "name_match_score": round(float(name_match_score), 4),
            "rating": round(float(rating), 2),
            "review_count": review_count,
            "is_permanently_closed": bool(is_permanently_closed),
            "is_operational": bool(is_operational),
            "address_match": bool(address_match),
            "place_url": place_url,
            "photo_reference": photo_reference,
            "maps_confidence": round(float(maps_confidence), 4),
            "continuity_from_maps": round(float(continuity_from_maps), 4),
            "mock_data": False,
            "provider": "google_maps",
        }

    async def _verify_business_on_osm(self, business_name: str, address: str, pin_code: str) -> dict:
        query = ", ".join([part for part in [business_name, address, pin_code, "India"] if str(part or "").strip()])
        user_agent = str(getattr(self.settings, "MAPS_USER_AGENT", "ShadowCredit/1.0") or "ShadowCredit/1.0")
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 5, "addressdetails": 1}
        headers = {"User-Agent": user_agent}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                results = resp.json() or []
            except Exception as exc:
                raise MapsVerificationError(f"Nominatim search failed: {exc}") from exc

        if not results:
            return {
                "place_found": False,
                "place_name": "",
                "name_match_score": 0.0,
                "rating": 0.0,
                "review_count": 0,
                "is_permanently_closed": False,
                "is_operational": False,
                "address_match": False,
                "place_url": "",
                "photo_reference": None,
                "maps_confidence": 0.0,
                "continuity_from_maps": 0.0,
                "mock_data": False,
                "provider": "osm_nominatim",
            }

        best = results[0]
        display_name = str(best.get("display_name") or "")
        place_name = str(best.get("name") or "").strip() or display_name.split(",")[0].strip()
        name_match_score = SequenceMatcher(None, business_name.lower().strip(), place_name.lower().strip()).ratio()
        address_match = str(pin_code or "").strip() in display_name
        importance = float(best.get("importance") or 0.0)
        osm_link = f"https://www.openstreetmap.org/?mlat={best.get('lat')}&mlon={best.get('lon')}"

        base = 0.55
        if name_match_score > 0.70:
            base += 0.20
        if address_match:
            base += 0.15
        base += min(importance, 1.0) * 0.10
        maps_confidence = min(base, 1.0)

        continuity_from_maps = 0.45 + min(importance, 1.0) * 0.30
        continuity_from_maps = max(0.0, min(1.0, continuity_from_maps))

        return {
            "place_found": True,
            "place_name": place_name,
            "name_match_score": round(float(name_match_score), 4),
            "rating": 0.0,
            "review_count": 0,
            "is_permanently_closed": False,
            "is_operational": True,
            "address_match": bool(address_match),
            "place_url": osm_link,
            "photo_reference": None,
            "maps_confidence": round(float(maps_confidence), 4),
            "continuity_from_maps": round(float(continuity_from_maps), 4),
            "mock_data": False,
            "provider": "osm_nominatim",
        }

    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        business_name = str(inputs.get("business_name") or "").strip()
        address = str(inputs.get("address") or "").strip()
        pin_code = str(inputs.get("pin_code") or "").strip()

        if not business_name:
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={},
                confidence_score=0.0,
                latency_ms=0,
                errors=["business_name is required"],
                warnings=[],
                fallback_used=False,
            )

        try:
            result = await self.verify_business_on_maps(business_name, address, pin_code)
            if result.get("mock_data"):
                await self._audit_mock_data(session_id, business_name, address, pin_code)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=True,
                data=result,
                confidence_score=float(result.get("maps_confidence", 0.0)),
                latency_ms=0,
                errors=[],
                warnings=[],
                fallback_used=bool(result.get("mock_data")),
            )
        except Exception as exc:
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={},
                confidence_score=0.0,
                latency_ms=0,
                errors=[str(exc)],
                warnings=[],
                fallback_used=False,
            )


# Compatibility alias
MapsVerifierAgent = GoogleMapsVerificationAgent


def verify_business_on_maps(business_name: str, address: str, pin_code: str) -> dict:
    """
    Convenience sync wrapper for script/test usage.
    Uses hackathon-safe fallback when API key/settings are unavailable.
    """
    agent = GoogleMapsVerificationAgent()
    result = agent._mock_result()
    result["name_match_score"] = round(
        SequenceMatcher(None, business_name.lower().strip(), result["place_name"].lower().strip()).ratio(),
        4,
    )
    return result
