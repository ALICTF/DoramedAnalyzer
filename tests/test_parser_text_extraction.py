from pathlib import Path

from pdf_extractor import PDFReportParser


SAMPLE_REPORTS_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_reports"


def test_body_composition_text_extraction():
    parser = PDFReportParser(api_key=None)
    result = parser.parse_file(
        (SAMPLE_REPORTS_DIR / "body_composition.pdf").read_bytes(),
        filename="body_composition.pdf",
    )

    assert result["type"] == "body_composition"
    assert result["error"] is None
    assert result["data"]["extraction_method"] == "text"
    assert result["data"]["weight_kg"] == 124.5
    assert result["ai_usage"]["used_ai"] is False


def test_blood_pressure_text_extraction():
    parser = PDFReportParser(api_key=None)
    result = parser.parse_file(
        (SAMPLE_REPORTS_DIR / "blood_pressure.pdf").read_bytes(),
        filename="blood_pressure.pdf",
    )

    assert result["type"] == "blood_pressure"
    assert result["error"] is None
    assert result["data"]["extraction_method"] == "text"
    assert result["data"]["systolic_mmhg"] == 123
    assert result["data"]["diastolic_mmhg"] == 66
    assert result["ai_usage"]["summary"]["calls"] == 0


def test_filename_is_used_as_validation_title_without_contaminating_content_detection():
    parser = PDFReportParser(api_key=None)
    result = parser.parse_file(
        (SAMPLE_REPORTS_DIR / "body_composition.pdf").read_bytes(),
        filename="blood_pressure.pdf",
    )

    assert result["data"] is None
    assert result["title_validation"]["status"] == "mismatch"
    assert result["title_validation"]["provided_title"] == "blood_pressure.pdf"
    assert result["title_validation"]["title_category"] == "blood_pressure"
    assert result["title_validation"]["content_category"] == "body_composition"
