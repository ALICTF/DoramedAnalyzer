from collections.abc import Callable
from typing import Optional

from core.logging_utils import compact_warning, get_logger
from services.document_classifier import MedicalDocumentClassifier
from validators.title_match import TitleValidation, check_title_matches_content, normalize_category


logger = get_logger("report_validation")


class ReportValidationError(ValueError):
    """Raised when the provided report title conflicts with file content."""

    def __init__(self, validation: TitleValidation) -> None:
        super().__init__(validation.message)
        self.validation = validation


class ReportValidationService:
    """Validate caller-provided report metadata before parsing the file."""

    def validate_title_and_content(
        self,
        *,
        provided_title: Optional[str],
        sample_text: str,
        pdf_bytes: bytes,
        filename: str,
        content_filename: Optional[str] = None,
        classifier: MedicalDocumentClassifier,
        identify_type: Callable[[str, str], str],
        detect_content_category_with_ai: Callable[[str, bytes, str, MedicalDocumentClassifier], str],
    ) -> TitleValidation:
        """Compare the user-selected title with the actual file content.

        The check has two parts:
        1. Normalize the title/report name sent by the caller.
        2. Detect the category from file content and compare both categories.

        A mismatch raises ``ReportValidationError`` so the caller can handle it
        with a normal try/except flow before sending the file deeper into the
        parsing system.
        """
        try:
            validation = self._build_validation(
                provided_title=provided_title,
                sample_text=sample_text,
                pdf_bytes=pdf_bytes,
                filename=filename,
                content_filename=content_filename,
                classifier=classifier,
                identify_type=identify_type,
                detect_content_category_with_ai=detect_content_category_with_ai,
            )
        except ReportValidationError:
            raise
        except Exception as exc:
            compact_warning(logger, "Report validation", exc, file=filename)
            validation = check_title_matches_content(provided_title, "unknown")

        if validation.is_mismatch:
            logger.error(
                "Report validation failed. file=%s provided_title=%r title_category=%s content_category=%s reason=%s",
                filename or "unknown",
                validation.provided_title,
                validation.title_category,
                validation.content_category,
                validation.message,
            )
            raise ReportValidationError(validation)

        logger.info(
            "Report validation passed. file=%s status=%s title_category=%s content_category=%s",
            filename or "unknown",
            validation.status,
            validation.title_category,
            validation.content_category,
        )
        return validation

    def _build_validation(
        self,
        *,
        provided_title: Optional[str],
        sample_text: str,
        pdf_bytes: bytes,
        filename: str,
        content_filename: Optional[str],
        classifier: MedicalDocumentClassifier,
        identify_type: Callable[[str, str], str],
        detect_content_category_with_ai: Callable[[str, bytes, str, MedicalDocumentClassifier], str],
    ) -> TitleValidation:
        if not provided_title or not provided_title.strip():
            return check_title_matches_content(provided_title, None)

        content_category = identify_type(sample_text, content_filename if content_filename is not None else filename)

        # Spend an AI call only when the title is known but content heuristics
        # cannot categorize the file.
        if content_category == "unknown" and normalize_category(provided_title) is not None:
            content_category = detect_content_category_with_ai(sample_text, pdf_bytes, filename, classifier)

        return check_title_matches_content(provided_title, content_category)
