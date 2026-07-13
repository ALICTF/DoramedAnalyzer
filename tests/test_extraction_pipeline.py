from pipeline import ExtractionPipeline


class ListReturningParser:
    vision_client = None

    def _extract_pdf_text(self, pdf_bytes):
        return "some extracted text"

    def _parse_text(self, text):
        return [{"test": "WBC", "value": 8.8}]

    def _is_valid(self, data):
        return bool(data)

    def _convert_pdf_pages_to_base64(self, pdf_bytes):
        return iter(())

    def _parse_vision(self, image_base64):
        return {}

    def _extract_pdf_text_with_ocr(self, pdf_bytes):
        return ""


def test_pipeline_wraps_list_outputs():
    result = ExtractionPipeline(ListReturningParser()).run(b"pdf")

    assert result["extraction_method"] == "text"
    assert result["items"] == [{"test": "WBC", "value": 8.8}]
