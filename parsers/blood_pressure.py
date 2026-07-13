import json
from typing import Any, Dict, Optional

from core.logging_utils import compact_warning, get_logger
from core.patterns import PDFPatterns
from prompts.blood_pressure import build_blood_pressure_vision_prompt
from validators import is_valid_blood_pressure

from .base import BaseReportParser


logger = get_logger("bp_parser")


class BloodPressureParser(BaseReportParser):
    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        data = self.apply_regex_patterns(text, PDFPatterns.BP_PATTERNS)

        date_match = PDFPatterns.BP_DATE_PATTERN.search(text)
        bp_matches = PDFPatterns.BP_MEASUREMENT_PATTERN.findall(text)
        pulse_matches = PDFPatterns.BP_PULSE_PATTERN.findall(text)

        if bp_matches:
            try:
                if date_match:
                    data["measurement_date"] = date_match.group(1)

                latest_bp = bp_matches[-1]
                data["systolic_mmhg"] = int(latest_bp[0])
                data["diastolic_mmhg"] = int(latest_bp[1])

                if pulse_matches:
                    data["pulse_bpm"] = int(pulse_matches[-1])

                data["map_mmhg"] = int(
                    data["diastolic_mmhg"] + (1 / 3 * (data["systolic_mmhg"] - data["diastolic_mmhg"]))
                )
            except ValueError as exc:
                compact_warning(logger, "Blood pressure text parsing", exc)

        return data if data else None

    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        return is_valid_blood_pressure(data)

    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        logger.info("Vision request started. parser=blood_pressure")
        response = self.vision_client.chat.completions.create(
            model=self.settings.vision_model,
            response_format={"type": "json_object"},
            temperature=self.settings.llm_temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_blood_pressure_vision_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    ],
                }
            ],
        )
        self._record_ai_usage(
            response,
            operation="blood_pressure.vision_extraction",
            requested_model=self.settings.vision_model,
        )
        return json.loads(response.choices[0].message.content)
