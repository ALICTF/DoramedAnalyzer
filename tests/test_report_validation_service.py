import pytest

from services.document_classifier import MedicalDocumentClassifier
from services.report_validation import ReportValidationError, ReportValidationService


def test_validation_service_accepts_matching_title_and_content():
    service = ReportValidationService()

    result = service.validate_title_and_content(
        provided_title="Blood Pressure Report",
        sample_text="SYS 123 DIA 66 mmHg",
        pdf_bytes=b"pdf",
        filename="report.pdf",
        classifier=MedicalDocumentClassifier(client=None),
        identify_type=lambda text, filename: "blood_pressure",
        detect_content_category_with_ai=lambda *args: "unknown",
    )

    assert result.status == "match"


def test_validation_service_raises_when_title_and_content_mismatch():
    service = ReportValidationService()

    with pytest.raises(ReportValidationError) as raised:
        service.validate_title_and_content(
            provided_title="Blood Pressure Report",
            sample_text="oxygen level avg 96",
            pdf_bytes=b"pdf",
            filename="report.pdf",
            classifier=MedicalDocumentClassifier(client=None),
            identify_type=lambda text, filename: "oxygen_level",
            detect_content_category_with_ai=lambda *args: "unknown",
        )

    validation = raised.value.validation
    assert validation.is_mismatch
    assert validation.title_category == "blood_pressure"
    assert validation.content_category == "oxygen_level"


def test_validation_service_can_ignore_filename_when_detecting_content():
    service = ReportValidationService()
    seen = {}

    def identify_type(text, filename):
        seen["filename"] = filename
        return "oxygen_level"

    with pytest.raises(ReportValidationError):
        service.validate_title_and_content(
            provided_title="blood_pressure.pdf",
            sample_text="oxygen level avg 96",
            pdf_bytes=b"pdf",
            filename="blood_pressure.pdf",
            content_filename="",
            classifier=MedicalDocumentClassifier(client=None),
            identify_type=identify_type,
            detect_content_category_with_ai=lambda *args: "unknown",
        )

    assert seen["filename"] == ""
