from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Absolute path to the project root (two levels up from backend/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = str(_PROJECT_ROOT / "data" / "shadow_credit.db")

_ENV_FILE = Path(__file__).resolve().with_name(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",         # ignore unknown env vars
        case_sensitive=False    # MASTER_ENCRYPTION_KEY = master_encryption_key
    )

    # ── Application ────────────────────────────────────────────
    APP_NAME: str = "Shadow Credit"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # "development" | "staging" | "production"

    # ── Security ───────────────────────────────────────────────
    # 64-character hex string representing 256-bit AES key.
    # NO default — must be explicitly set. System refuses to start without it.
    MASTER_ENCRYPTION_KEY: str

    # ── Database ───────────────────────────────────────────────
    # Default is an absolute path anchored to this file's location so the
    # server works correctly regardless of the CWD it is launched from.
    # If you override via .env, relative paths are resolved to absolute
    # automatically by the validator below.
    DATABASE_PATH: str = _DEFAULT_DB_PATH

    # ── External APIs ──────────────────────────────────────────
    ANTHROPIC_API_KEY: str = "AQK125466T47RT734Y8TY945U"    # Deprecated; retained for backward compatibility
    GROQ_API_KEY: str = "GQk1Z2V0aW5nX2tleV9leGFtcGxl"  # Placeholder; replace with your actual key
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    SUPERVISOR_REASONING_PROVIDER: str = "rule_based"  # rule_based | groq
    GOOGLE_VISION_CREDENTIALS_PATH: str = ""   # Optional — fallback only
    GOOGLE_MAPS_API_KEY: str = "GKM264T347589397788887"
    MAPS_PROVIDER: str = "osm"  #  | google | osm | auto
    MAPS_USER_AGENT: str = "ShadowCredit/1.0"

    # ── OCR Behavior ───────────────────────────────────────────
    OCR_CONFIDENCE_THRESHOLD: float = 0.60
    USE_GPU: bool = False
    PADDLE_LANG: list[str] = ["en", "hi"]
    ENABLE_EASYOCR_FALLBACK: bool = True
    EASYOCR_LANGS: str = "en,hi"
    EASYOCR_GPU: bool = False
    ENABLE_GOOGLE_VISION_FALLBACK: bool = False
    ENABLE_TESSERACT_FALLBACK: bool = False
    TESSERACT_CMD: str = ""
    TESSERACT_LANGS: str = "eng+hin"

    # ── Confidence Thresholds ──────────────────────────────────
    CONFIDENCE_HIGH_THRESHOLD: float = 0.85    # AUTO_ACCEPT above this
    CONFIDENCE_MEDIUM_THRESHOLD: float = 0.50  # CLARIFY between this and HIGH

    # ── Credit Formula ─────────────────────────────────────────
    CREDIT_MULTIPLIER: float = 3.0              # 3× median monthly
    CREDIT_CAP_WITHOUT_AA: float = 300000.0     # ₹3,00,000
    CREDIT_CAP_WITH_AA: float = 1000000.0       # ₹10,00,000
    CREDIT_ROUNDING: int = 5000                 # round to nearest ₹5,000

    # ── Network ────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── WebSocket ──────────────────────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 10     # seconds - keep connection alive
    WS_MAX_EVENT_HISTORY: int = 50      # events to replay on reconnect

    # ── Rate Limiting ──────────────────────────────────────────
    RATE_LIMIT_INGEST: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # ── Agent Timeouts ─────────────────────────────────────────
    TIMEOUT_OCR_AGENT: int = 30
    TIMEOUT_WHATSAPP_AGENT: int = 45
    TIMEOUT_KHATA_AGENT: int = 15
    TIMEOUT_WARMTH_AGENT: int = 20
    TIMEOUT_RECONCILIATION_AGENT: int = 15
    TIMEOUT_COMPLIANCE_AGENT: int = 10
    TIMEOUT_REPORT_AGENT: int = 20

    # ── Validators ─────────────────────────────────────────────
    @field_validator("DATABASE_PATH", mode="before")
    @classmethod
    def resolve_db_path(cls, v: str) -> str:
        """Resolve a relative DATABASE_PATH to absolute.

        Relative paths in .env are interpreted as relative to the backend/
        directory (where config.py lives), which is the conventional launch
        directory for the server. This makes the resolved path CWD-agnostic.
        """
        p = Path(v)
        if not p.is_absolute():
            # Anchor to backend/ (config.py's own directory)
            p = (Path(__file__).resolve().parent / p).resolve()
        return str(p)

    @field_validator("MASTER_ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError(
                f"MASTER_ENCRYPTION_KEY must be exactly 64 hex characters "
                f"(256-bit key). Got {len(v)} characters."
            )
        try:
            bytes.fromhex(v)
        except ValueError:
            raise ValueError("MASTER_ENCRYPTION_KEY must be valid hexadecimal.")
        return v

    @field_validator("CONFIDENCE_HIGH_THRESHOLD", "CONFIDENCE_MEDIUM_THRESHOLD")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence thresholds must be between 0.0 and 1.0")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Returns cached Settings instance. lru_cache means this is only instantiated once per process."""
    return Settings()
