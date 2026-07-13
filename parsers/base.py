# parsers/base.py
import fitz
import base64
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Pattern
from core.ai_usage import AIUsageTracker
from core.logging_utils import compact_warning, compact_error, get_logger
from core.settings import get_settings
from pipeline import ExtractionPipeline

logger = get_logger("base_parser")

class BaseReportParser(ABC):
    
    def __init__(self, vision_client: Any, usage_tracker: Optional[AIUsageTracker] = None) -> None:
        self.vision_client = vision_client
        self.usage_tracker = usage_tracker
        self.settings = get_settings()
        self.max_vision_pages = self.settings.max_vision_pages
        self.last_audit = None

    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        pipeline = ExtractionPipeline(self)
        result = pipeline.run(pdf_bytes)
        self.last_audit = pipeline.audit
        return result

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                text = "\n".join(page.get_text("text") for page in doc)
            return text.strip()
        except Exception as e:
            compact_warning(logger, "PDF text extraction", e)
            return ""

    def _convert_pdf_to_base64(self, pdf_bytes: bytes) -> str:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                first_page = doc[0]
                pixmap = first_page.get_pixmap(dpi=self.settings.pdf_render_dpi)
                img_buffer = pixmap.tobytes("png")
                return base64.b64encode(img_buffer).decode('utf-8')
        except Exception as e:
            compact_error(logger, "PDF page rendering", e)
            raise

    def _convert_pdf_pages_to_base64(self, pdf_bytes: bytes):
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                page_count = min(doc.page_count, self.max_vision_pages)
                for page_index in range(page_count):
                    pixmap = doc[page_index].get_pixmap(dpi=self.settings.pdf_render_dpi)
                    img_buffer = pixmap.tobytes("png")
                    yield page_index, base64.b64encode(img_buffer).decode("utf-8")
        except Exception as e:
            compact_error(logger, "PDF page rendering", e)
            raise

    def _extract_pdf_text_with_ocr(self, pdf_bytes: bytes) -> str:
        if not self.settings.ocr_enabled:
            logger.info("OCR skipped. reason=disabled")
            return ""

        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                ocr_pages = []
                for page in doc:
                    textpage = page.get_textpage_ocr(flags=0, dpi=self.settings.ocr_dpi, full=True)
                    ocr_pages.append(page.get_text("text", textpage=textpage))
            return "\n".join(ocr_pages).strip()
        except Exception as e:
            compact_warning(logger, "OCR extraction", e)
            return ""

    def apply_regex_patterns(self, text: str, pattern_dict: Dict[str, Tuple[Pattern, type]]) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, (pattern, cast_type) in pattern_dict.items():
            match = pattern.search(text)
            if match:
                try:
                    val = match.group(1).replace(",", "").strip()
                    data[key] = cast_type(val)
                except (ValueError, IndexError):
                    logger.debug("Regex value skipped. key=%s reason=cast_failed", key)
                    continue
        return data

    def _record_ai_usage(self, response: Any, *, operation: str, requested_model: str) -> None:
        if self.usage_tracker is not None:
            self.usage_tracker.record_response(
                response,
                operation=operation,
                requested_model=requested_model,
            )

    @abstractmethod
    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        pass
