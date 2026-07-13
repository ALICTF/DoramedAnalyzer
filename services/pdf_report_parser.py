import fitz
from typing import Dict, Any, Optional
from openai import OpenAI
from core.ai_usage import AIUsageTracker
from core.logging_utils import compact_warning, compact_error, get_logger, setup_logging
from core.settings import get_settings

from parsers.body_composition import BodyCompositionParser
from parsers.blood_pressure import BloodPressureParser
from parsers.oxygen import OxygenLevelParser
from parsers.ecg import ECGParser
from parsers.generic import GenericMedicalParser
from services.document_classifier import MedicalDocumentClassifier

logger = get_logger("pdf_extractor")

class PDFReportParser:

    FILE_KEYWORDS_O2 = ["o2", "oxygen", "اکسیژن"]
    FILE_KEYWORDS_ECG = ["ecg", "heart", "نوار قلب"]
    FILE_KEYWORDS_BC = ["body", "composition", "inbody", "آنالیز"]
    FILE_KEYWORDS_BP = ["blood", "pressure", "bp", "فشار"]

    TEXT_KEYWORDS_BC = ["fat mass", "smm", "body score", "muscle"]
    TEXT_KEYWORDS_BP = ["sys", "dia", "mmhg", "فشار خون"]
    TEXT_KEYWORDS_O2 = ["oxygen level", "o2 score"]
    TEXT_KEYWORDS_ECG = ["sinus rhythm", "rhythm status"]

    def __init__(self, api_key: Optional[str] = None):
        setup_logging()
        self.settings = get_settings()
        self.api_key = api_key or self.settings.api_key
        self.client = OpenAI(base_url=self.settings.openai_base_url, api_key=self.api_key) if self.api_key else None
            
        logger.info("Parser initialized. vision_enabled=%s", bool(self.client))

    def _identify_type(self, text: str, filename: str) -> str:
        text_lower = text.lower()
        fname_lower = filename.lower()
        
        if any(k in fname_lower for k in self.FILE_KEYWORDS_O2): return "oxygen_level"
        if any(k in fname_lower for k in self.FILE_KEYWORDS_ECG): return "ecg"

        scores = {"body_composition": 0, "blood_pressure": 0}

        if any(k in fname_lower for k in self.FILE_KEYWORDS_BC): scores["body_composition"] += 2
        if any(k in fname_lower for k in self.FILE_KEYWORDS_BP): scores["blood_pressure"] += 2

        if any(k in text_lower for k in self.TEXT_KEYWORDS_BC): scores["body_composition"] += 1
        if any(k in text_lower for k in self.TEXT_KEYWORDS_BP): scores["blood_pressure"] += 1


        if scores["body_composition"] > scores["blood_pressure"]: return "body_composition"
        if scores["blood_pressure"] > scores["body_composition"]: return "blood_pressure"

        if any(k in text_lower for k in self.TEXT_KEYWORDS_O2): return "oxygen_level"
        if any(k in text_lower for k in self.TEXT_KEYWORDS_ECG): return "ecg"

        if scores["body_composition"] > 0: return "body_composition"

        return "unknown"

    def parse_file(self, pdf_bytes: bytes, filename: str = "", frontend_test_name: Optional[str] = None) -> Dict[str, Any]:

        logger.info("Parse started. file=%s", filename or "unknown")
        usage_tracker = AIUsageTracker(provider="gapgpt")
        parsers = self._build_parsers(usage_tracker)
        classifier = MedicalDocumentClassifier(self.client, usage_tracker=usage_tracker)
        
        sample_text = ""
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                sample_pages = min(doc.page_count, self.settings.pdf_sample_pages)
                sample_text = "\n".join(doc[index].get_text("text") for index in range(sample_pages))
        except Exception as e:
            compact_warning(logger, "Sample text extraction", e, file=filename)
            
        report_type = frontend_test_name if frontend_test_name else self._identify_type(sample_text, filename)
        
        if report_type in parsers:
            logger.info("Parser selected. type=%s strategy=dedicated", report_type)
            parser = parsers[report_type]
        else:
            classification = self._classify_generic_document(
                pdf_bytes,
                sample_text,
                filename,
                report_type,
                classifier,
                usage_tracker,
            )
            if report_type != "unknown":
                report_type = report_type
            elif classification.confidence >= self.settings.classification_min_confidence:
                report_type = classification.document_type
            else:
                report_type = "Unknown Medical Report"
            logger.info(
                "Parser selected. type=%s strategy=generic confidence=%.2f",
                report_type,
                classification.confidence,
            )
            parser = GenericMedicalParser(
                self.client,
                test_name=report_type,
                classification=classification,
                usage_tracker=usage_tracker,
            )

        try:
            result = parser.parse(pdf_bytes)
        except Exception as e:
            compact_error(logger, "Parser execution", e, file=filename, type=report_type)
            result = {"error": str(e)}
        
        has_error = "error" in result
        if has_error:
            logger.error("Parse finished with error. file=%s reason=%s", filename or "unknown", result.get("error"))
        else:
            method = result.get("extraction_method") if isinstance(result, dict) else None
            logger.info("Parse finished. file=%s method=%s", filename or "unknown", method or "unknown")
        
        return {
            "type": report_type,
            "filename": filename,
            "data": result if not has_error else None,
            "error": result.get("error") if has_error else None,
            "ai_usage": usage_tracker.to_dict(),
        }

    def _build_parsers(self, usage_tracker: AIUsageTracker) -> Dict[str, Any]:
        return {
            "body_composition": BodyCompositionParser(self.client, usage_tracker=usage_tracker),
            "blood_pressure": BloodPressureParser(self.client, usage_tracker=usage_tracker),
            "oxygen_level": OxygenLevelParser(self.client, usage_tracker=usage_tracker),
            "ecg": ECGParser(self.client, usage_tracker=usage_tracker),
        }

    def _classify_generic_document(
        self,
        pdf_bytes: bytes,
        sample_text: str,
        filename: str,
        report_type: str,
        classifier: MedicalDocumentClassifier,
        usage_tracker: AIUsageTracker,
    ):
        if report_type and report_type != "unknown":
            return classifier.fallback(filename=report_type, reason="Document type was provided by caller.")

        if sample_text.strip():
            return classifier.classify_text(sample_text, filename=filename)

        if self.client:
            try:
                generic_parser = GenericMedicalParser(
                    self.client,
                    test_name="Unknown Medical Document",
                    usage_tracker=usage_tracker,
                )
                first_page = next(generic_parser._convert_pdf_pages_to_base64(pdf_bytes), None)
                if first_page:
                    _, image_base64 = first_page
                    return classifier.classify_vision(image_base64, filename=filename)
            except Exception as exc:
                compact_warning(logger, "Generic document classification", exc, file=filename)

        return classifier.fallback(filename=filename, reason="No text or vision input was available.")
