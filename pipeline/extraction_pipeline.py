from typing import Any, Dict, Optional, Protocol

from core.logging_utils import compact_error, get_logger
from models import ExtractionAudit


logger = get_logger("extraction_pipeline")


class ParserStrategy(Protocol):
    vision_client: Any

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        ...

    def _extract_pdf_text_with_ocr(self, pdf_bytes: bytes) -> str:
        ...

    def _convert_pdf_pages_to_base64(self, pdf_bytes: bytes):
        ...

    def _parse_text(self, text: str) -> Optional[Dict[str, Any]]:
        ...

    def _parse_vision(self, image_base64: str) -> Dict[str, Any]:
        ...

    def _is_valid(self, data: Optional[Dict[str, Any]]) -> bool:
        ...


class ExtractionPipeline:
    def __init__(self, parser: ParserStrategy) -> None:
        self.parser = parser
        self.audit = ExtractionAudit()

    def run(self, pdf_bytes: bytes) -> Dict[str, Any]:
        text_data = self._try_text(pdf_bytes)
        if self.parser._is_valid(text_data):
            self.audit.add_step("text", "success")
            logger.info("Extraction succeeded. method=text")
            return self._finalize(text_data, "text")
        self.audit.add_step("text", "failed", reason="validation_failed")

        vision_data = self._try_vision(pdf_bytes, text_data)
        if self.parser._is_valid(vision_data):
            return self._finalize(vision_data, "vision")

        ocr_data = self._try_ocr(pdf_bytes, text_data)
        if self.parser._is_valid(ocr_data):
            self.audit.add_step("ocr", "success")
            logger.info("Extraction succeeded. method=ocr")
            return self._finalize(ocr_data, "ocr")
        self.audit.add_step("ocr", "failed", reason="validation_failed")

        if not self.parser.vision_client:
            return {"error": "Text extraction failed and Vision API client is not configured."}
        return {"error": "Text, Vision API, and OCR failed to extract valid data from the document."}

    def _try_text(self, pdf_bytes: bytes) -> Optional[Dict[str, Any]]:
        text = self.parser._extract_pdf_text(pdf_bytes)
        return self.parser._parse_text(text) if text else None

    def _try_vision(self, pdf_bytes: bytes, partial_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        logger.info("Extraction fallback. from=text to=vision")

        if not self.parser.vision_client:
            logger.warning("Vision skipped. reason=client_not_configured")
            self.audit.add_step("vision", "skipped", reason="client_not_configured")
            return None

        try:
            for page_index, image_base64 in self.parser._convert_pdf_pages_to_base64(pdf_bytes):
                vision_data = self.parser._parse_vision(image_base64)
                if self.parser._is_valid(vision_data):
                    self.audit.add_step("vision", "success", page=page_index + 1)
                    logger.info("Extraction succeeded. method=vision page=%s", page_index + 1)
                    if partial_data:
                        return {**partial_data, **vision_data}
                    return vision_data

            logger.warning("Vision returned invalid data. reason=validation_failed")
            self.audit.add_step("vision", "failed", reason="validation_failed")
            return None
        except Exception as exc:
            compact_error(logger, "Vision extraction", exc)
            self.audit.add_step("vision", "failed", reason=str(exc) or exc.__class__.__name__)
            return None

    def _try_ocr(self, pdf_bytes: bytes, partial_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        logger.info("Extraction fallback. from=vision to=ocr")
        ocr_text = self.parser._extract_pdf_text_with_ocr(pdf_bytes)
        ocr_data = self.parser._parse_text(ocr_text) if ocr_text else None
        if partial_data and ocr_data:
            return {**partial_data, **ocr_data}
        return ocr_data

    def _finalize(self, data: Optional[Dict[str, Any]], method: str) -> Dict[str, Any]:
        if data is None:
            return {"error": f"{method} extraction produced no data."}
        if isinstance(data, list):
            data = {"items": data}
        if not isinstance(data, dict):
            data = {"value": data}
        data["extraction_method"] = method
        return data
