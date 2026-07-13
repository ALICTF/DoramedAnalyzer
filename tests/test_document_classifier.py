from services.document_classifier import MedicalDocumentClassifier


def test_classifier_fallback_uses_filename():
    classifier = MedicalDocumentClassifier(client=None)
    result = classifier.fallback(filename="brain_mri.pdf", reason="offline")

    assert result.document_type == "Brain Mri"
    assert result.is_medical is True
    assert result.confidence == 0.2
    assert result.reason == "offline"


def test_classifier_without_client_does_not_fail():
    classifier = MedicalDocumentClassifier(client=None)
    result = classifier.classify_text("Complete blood count report with WBC and RBC values.", filename="cbc.pdf")

    assert result.document_type == "Cbc"
    assert result.confidence == 0.2


def test_low_confidence_generic_keeps_unknown_public_type():
    from pdf_extractor import PDFReportParser

    parser = PDFReportParser(api_key=None)
    result = parser.parse_file(b"not a pdf", filename="mystery.pdf")

    assert result["type"] == "Unknown Medical Report"
