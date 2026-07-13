import json
from typing import Any, Dict, Optional

from core.ai_usage import AIUsageTracker
from core.logging_utils import compact_warning, get_logger
from services.document_classifier import DocumentClassification
from prompts.generic import build_generic_text_prompt, build_generic_vision_prompt

from .base import BaseReportParser


logger = get_logger("generic_parser")


class GenericMedicalParser(BaseReportParser):
    def __init__(
        self,
        vision_client: Any,
        test_name: str,
        classification: Optional[DocumentClassification] = None,
        usage_tracker: Optional[AIUsageTracker] = None,
    ) -> None:
        super().__init__(vision_client, usage_tracker=usage_tracker)
        self.test_name = test_name
        self.ai_client = vision_client
        self.classification = classification or DocumentClassification(
            document_type=test_name,
            modality=None,
            body_region=None,
            specialty=None,
            language=None,
            is_medical=True,
            confidence=0.0,
            reason="Classification was not provided.",
        )

    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or len(text.strip()) < 50:
            logger.info("Text LLM skipped. reason=text_too_short")
            return None

        try:
            logger.info("Text LLM request started. test_name=%s", self.test_name)
            response = self.ai_client.chat.completions.create(
                model=self.settings.generic_text_model,
                response_format={"type": "json_object"},
                temperature=self.settings.llm_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": build_generic_text_prompt(
                            document_type=self.classification.document_type,
                            modality=self.classification.modality,
                            body_region=self.classification.body_region,
                            specialty=self.classification.specialty,
                            text=text,
                        ),
                    }
                ],
            )
            self._record_ai_usage(
                response,
                operation="generic.text_extraction",
                requested_model=self.settings.generic_text_model,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as exc:
            compact_warning(logger, "Text LLM extraction", exc, test_name=self.test_name)
            return None

    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        return bool(data)

    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        logger.info("Vision request started. parser=generic test_name=%s", self.test_name)
        response = self.ai_client.chat.completions.create(
            model=self.settings.vision_model,
            response_format={"type": "json_object"},
            temperature=self.settings.llm_temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": build_generic_vision_prompt(
                                document_type=self.classification.document_type,
                                modality=self.classification.modality,
                                body_region=self.classification.body_region,
                                specialty=self.classification.specialty,
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    ],
                }
            ],
        )
        self._record_ai_usage(
            response,
            operation="generic.vision_extraction",
            requested_model=self.settings.vision_model,
        )
        return json.loads(response.choices[0].message.content)
