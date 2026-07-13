import json
from typing import Any, Dict, Optional

from core.logging_utils import get_logger
from core.patterns import PDFPatterns
from prompts.body_composition import build_body_composition_vision_prompt
from validators import is_valid_body_composition

from .base import BaseReportParser


logger = get_logger("body_composition_parser")


class BodyCompositionParser(BaseReportParser):
    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        data = self.apply_regex_patterns(text, PDFPatterns.BC_PATTERNS)

        if "bmi" not in data and "weight_kg" in data and "height_cm" in data:
            try:
                height_m = data["height_cm"] / 100.0
                data["bmi"] = round(data["weight_kg"] / (height_m**2), 1)
            except ZeroDivisionError:
                logger.warning("BMI calculation skipped. reason=height_zero")

        return data if data else None

    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        return is_valid_body_composition(data)

    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        logger.info("Vision request started. parser=body_composition")
        response = self.vision_client.chat.completions.create(
            model=self.settings.vision_model,
            response_format={"type": "json_object"},
            temperature=self.settings.llm_temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_body_composition_vision_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    ],
                }
            ],
        )
        self._record_ai_usage(
            response,
            operation="body_composition.vision_extraction",
            requested_model=self.settings.vision_model,
        )
        return json.loads(response.choices[0].message.content)
