import json
import re
from typing import Any, Dict, Optional

from core.logging_utils import get_logger
from core.patterns import PDFPatterns
from prompts.oxygen import build_oxygen_vision_prompt
from validators import is_valid_oxygen

from .base import BaseReportParser


logger = get_logger("o2_parser")


class OxygenLevelParser(BaseReportParser):
    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        data = self.apply_regex_patterns(text, PDFPatterns.O2_PATTERNS)
        normalized_text = re.sub(r"\s+", " ", text)

        o2_score = re.search(r"\bO2\s*Score\s*[:\-]?\s*(\d{1,3})\b", normalized_text, re.IGNORECASE)
        if o2_score:
            data.setdefault("session", {})["o2_score"] = int(o2_score.group(1))

        summary = self._extract_summary(normalized_text, ("oxygen", "spo2", "o2"))
        if summary:
            data["oxygen_summary"] = summary

        pulse_summary = self._extract_summary(normalized_text, ("pulse", "heart rate", "pr"))
        if pulse_summary:
            data["pulse_rate_summary"] = pulse_summary

        return data if data else None

    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        return is_valid_oxygen(data)

    def _extract_summary(self, text: str, labels: tuple) -> Optional[Dict[str, int]]:
        label_pattern = "|".join(re.escape(label) for label in labels)
        patterns = [
            rf"(?:{label_pattern}).{{0,80}}?max(?:imum)?\D+(\d{{1,3}}).{{0,40}}?avg(?:erage)?\D+(\d{{1,3}}).{{0,40}}?min(?:imum)?\D+(\d{{1,3}})",
            rf"(?:{label_pattern}).{{0,80}}?min(?:imum)?\D+(\d{{1,3}}).{{0,40}}?avg(?:erage)?\D+(\d{{1,3}}).{{0,40}}?max(?:imum)?\D+(\d{{1,3}})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            values = [int(value) for value in match.groups()]
            if "min" in pattern.split("\\D+")[0]:
                return {"min": values[0], "avg": values[1], "max": values[2]}
            return {"max": values[0], "avg": values[1], "min": values[2]}

        return None

    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        logger.info("Vision request started. parser=oxygen")
        response = self.vision_client.chat.completions.create(
            model=self.settings.vision_model,
            response_format={"type": "json_object"},
            temperature=self.settings.llm_temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_oxygen_vision_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    ],
                }
            ],
        )
        self._record_ai_usage(
            response,
            operation="oxygen.vision_extraction",
            requested_model=self.settings.vision_model,
        )
        return json.loads(response.choices[0].message.content)
