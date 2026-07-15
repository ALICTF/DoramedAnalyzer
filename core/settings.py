import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


def load_env_file(path: Optional[str] = None) -> None:
    """Load simple KEY=VALUE entries from a local .env file if present."""
    env_path = Path(path or ".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _get_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_model_pricing() -> Dict[str, Dict[str, float]]:
    pricing: Dict[str, Dict[str, float]] = {
        "qwen3-235b-a22b": {"input_per_1m": 0.16, "output_per_1m": 0.48},
        "gemini-2.5-flash-lite": {"input_per_1m": 0.10, "output_per_1m": 0.40},
        "gemini-3.1-flash-lite": {"input_per_1m": 0.25, "output_per_1m": 1.50},
        "gemini-3.5-flash": {"input_per_1m": 1.50, "output_per_1m": 9.00},
        "gpt-4o-mini": {"input_per_1m": 0.15, "output_per_1m": 0.60},
    }
    raw_value = os.environ.get("DSTAND_MODEL_PRICING", "")
    if not raw_value.strip():
        return pricing

    for item in raw_value.split(";"):
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3:
            continue
        model, input_price, output_price = parts
        try:
            pricing[model] = {
                "input_per_1m": float(input_price),
                "output_per_1m": float(output_price),
            }
        except ValueError:
            continue
    return pricing


@dataclass(frozen=True)
class AppSettings:
    api_key: Optional[str]
    openai_base_url: str
    vision_model: str
    vision_fallback_model: str
    vision_premium_model: str
    generic_text_model: str
    max_vision_pages: int
    pdf_sample_pages: int
    pdf_render_dpi: int
    ocr_dpi: int
    ocr_enabled: bool
    llm_temperature: float
    classification_min_confidence: float
    model_pricing_usd_per_1m_tokens: Dict[str, Dict[str, float]]
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    load_env_file()
    return AppSettings(
        api_key=os.environ.get("GAPGPT_API_KEY"),
        openai_base_url=os.environ.get("GAPGPT_BASE_URL", "https://api.gapgpt.app/v1"),
        vision_model=os.environ.get("DSTAND_VISION_MODEL", "gemini-2.5-flash-lite"),
        vision_fallback_model=os.environ.get("DSTAND_VISION_FALLBACK_MODEL", "gemini-3.1-flash-lite"),
        vision_premium_model=os.environ.get("DSTAND_VISION_PREMIUM_MODEL", "gemini-3.5-flash"),
        generic_text_model=os.environ.get("DSTAND_TEXT_MODEL", "qwen3-235b-a22b"),
        max_vision_pages=_get_int("DSTAND_MAX_VISION_PAGES", 3),
        pdf_sample_pages=_get_int("DSTAND_PDF_SAMPLE_PAGES", 3),
        pdf_render_dpi=_get_int("DSTAND_PDF_RENDER_DPI", 150),
        ocr_dpi=_get_int("DSTAND_OCR_DPI", 200),
        ocr_enabled=_get_bool("DSTAND_OCR_ENABLED", True),
        llm_temperature=_get_float("DSTAND_LLM_TEMPERATURE", 0.0),
        classification_min_confidence=_get_float("DSTAND_CLASSIFICATION_MIN_CONFIDENCE", 0.6),
        model_pricing_usd_per_1m_tokens=_get_model_pricing(),
        log_level=os.environ.get("DSTAND_LOG_LEVEL", "INFO").upper(),
    )
