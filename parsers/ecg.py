import json
import re
from typing import Any, Dict, Optional

from core.logging_utils import get_logger
from core.patterns import PDFPatterns
from prompts.ecg import build_ecg_vision_prompt
from validators import is_valid_ecg

from .base import BaseReportParser


logger = get_logger("ecg_parser")


class ECGParser(BaseReportParser):
    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        data = self.apply_regex_patterns(text, PDFPatterns.ECG_PATTERNS)

        if "heart_rate_bpm" not in data:
            hr_match = re.search(
                r"\b(?:HR|Heart\s*Rate|Pulse)\s*[:\-]?\s*(\d{2,3})\s*(?:bpm|/min)?\b",
                text,
                re.IGNORECASE,
            )
            if hr_match:
                data["heart_rate_bpm"] = int(hr_match.group(1))

        rhythm_match = re.search(
            r"\b(?:Rhythm|Rhythm\s*Status|Conclusion|Result)\s*[:\-]?\s*([^\n\r]{3,80})",
            text,
            re.IGNORECASE,
        )
        if rhythm_match:
            data["waveform_analysis"] = {"rhythm_regularity": rhythm_match.group(1).strip()}

        return data if data else None

    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        return is_valid_ecg(data)

    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        logger.info("Vision request started. parser=ecg")
        response = self.vision_client.chat.completions.create(
            model=self.settings.vision_model,
            response_format={"type": "json_object"},
            temperature=self.settings.llm_temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_ecg_vision_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    ],
                }
            ],
        )
        self._record_ai_usage(
            response,
            operation="ecg.vision_extraction",
            requested_model=self.settings.vision_model,
        )
        return json.loads(response.choices[0].message.content)
