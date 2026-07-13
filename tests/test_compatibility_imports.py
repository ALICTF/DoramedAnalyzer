from analyzer import HealthAnalyzer
from config import HealthConfig
from pdf_extractor import PDFReportParser


def test_legacy_imports_still_work():
    assert PDFReportParser.__name__ == "PDFReportParser"
    assert HealthAnalyzer.__name__ == "HealthAnalyzer"
    assert HealthConfig.__name__ == "HealthConfig"
