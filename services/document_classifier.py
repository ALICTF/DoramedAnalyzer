import json
from dataclasses import dataclass
from typing import Any, Optional

from core.ai_usage import AIUsageTracker
from core.logging_utils import compact_warning, get_logger
from core.settings import get_settings
from prompts.generic import build_classification_text_prompt, build_classification_vision_prompt


logger = get_logger("document_classifier")


@dataclass(frozen=True)
class DocumentClassification:
    document_type: str
    modality: Optional[str]
    body_region: Optional[str]
    specialty: Optional[str]
    language: Optional[str]
    is_medical: bool
    confidence: float
    reason: str


class MedicalDocumentClassifier:
    def __init__(self, client: Any, usage_tracker: Optional[AIUsageTracker] = None) -> None:
        self.client = client
        self.usage_tracker = usage_tracker
        self.settings = get_settings()

    def classify_text(self, text: str, filename: str = "") -> DocumentClassification:
        if not self.client:
            return self._fallback(filename, "AI client is not configured.")
        if not text or len(text.strip()) < 30:
            return self._fallback(filename, "Text sample is too short.")

        try:
            logger.info("Classification request started. mode=text file=%s", filename or "unknown")
            response = self.client.chat.completions.create(
                model=self.settings.generic_text_model,
                response_format={"type": "json_object"},
                temperature=self.settings.llm_temperature,
                messages=[{"role": "user", "content": build_classification_text_prompt(text, filename)}],
            )
            self._record_usage(
                response,
                operation="classification.text",
                requested_model=self.settings.generic_text_model,
            )
            return self._from_payload(json.loads(response.choices[0].message.content), filename)
        except Exception as exc:
            compact_warning(logger, "Text classification", exc, file=filename)
            return self._fallback(filename, str(exc) or exc.__class__.__name__)

    def classify_vision(self, image_base64: str, filename: str = "") -> DocumentClassification:
        if not self.client:
            return self._fallback(filename, "AI client is not configured.")

        try:
            logger.info("Classification request started. mode=vision file=%s", filename or "unknown")
            response = self.client.chat.completions.create(
                model=self.settings.vision_model,
                response_format={"type": "json_object"},
                temperature=self.settings.llm_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": build_classification_vision_prompt(filename)},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                        ],
                    }
                ],
            )
            self._record_usage(
                response,
                operation="classification.vision",
                requested_model=self.settings.vision_model,
            )
            return self._from_payload(json.loads(response.choices[0].message.content), filename)
        except Exception as exc:
            compact_warning(logger, "Vision classification", exc, file=filename)
            return self._fallback(filename, str(exc) or exc.__class__.__name__)

    def fallback(self, filename: str = "", reason: str = "Classification was not available.") -> DocumentClassification:
        return self._fallback(filename, reason)

    def _from_payload(self, payload: dict[str, Any], filename: str) -> DocumentClassification:
        confidence = payload.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        return DocumentClassification(
            document_type=str(payload.get("document_type") or self._guess_from_filename(filename)),
            modality=_optional_str(payload.get("modality")),
            body_region=_optional_str(payload.get("body_region")),
            specialty=_optional_str(payload.get("specialty")),
            language=_optional_str(payload.get("language")),
            is_medical=bool(payload.get("is_medical", True)),
            confidence=max(0.0, min(1.0, confidence)),
            reason=str(payload.get("reason") or "No reason provided."),
        )

    def _fallback(self, filename: str, reason: str) -> DocumentClassification:
        return DocumentClassification(
            document_type=self._guess_from_filename(filename),
            modality=None,
            body_region=None,
            specialty=None,
            language=None,
            is_medical=True,
            confidence=0.2 if filename else 0.0,
            reason=reason,
        )

    def _guess_from_filename(self, filename: str) -> str:
        cleaned = (filename or "").replace("_", " ").replace("-", " ").rsplit(".", 1)[0].strip()
        return cleaned.title() if cleaned else "Unknown Medical Document"

    def _record_usage(self, response: Any, *, operation: str, requested_model: str) -> None:
        if self.usage_tracker is not None:
            self.usage_tracker.record_response(
                response,
                operation=operation,
                requested_model=requested_model,
            )


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
