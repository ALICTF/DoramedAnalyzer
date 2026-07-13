import json
import os
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple

from analyzer import HealthAnalyzer
from core.ai_usage import aggregate_ai_usage
from pdf_extractor import PDFReportParser


DEFAULT_API_KEY: Final[str] = "sk-ER2rLVhErY64E5EYNwQ1LaF2VUk6VLqq9mlIyHC9HlJJKeCd"
SAMPLE_REPORTS_DIR: Final[Path] = Path(__file__).resolve().parent / "data" / "sample_reports"

TEST_CASES: Final[List[Tuple[str, Optional[str]]]] = [
    ("body_composition.pdf", None),
    ("blood_pressure.pdf", None),
    ("o2.pdf", None),
    ("ecg.pdf", None),
    ("CBC.pdf", "Complete Blood Count (CBC) - Blood Test"),
    ("inbody.pdf", "Generic Body Composition - Custom Scan"),
]


def run_integration_test() -> None:
    api_key = os.environ.get("GAPGPT_API_KEY", DEFAULT_API_KEY)
    parser = PDFReportParser(api_key=api_key)
    analyzer = HealthAnalyzer()
    results: List[Dict[str, Any]] = []

    print("Starting integration test suite.")
    print(f"Sample reports directory: {SAMPLE_REPORTS_DIR}")

    if api_key == DEFAULT_API_KEY:
        print("Warning: GAPGPT_API_KEY is not set. The fallback key will be used.")

    for file_name, frontend_test_name in TEST_CASES:
        file_path = SAMPLE_REPORTS_DIR / file_name
        print("-" * 72)
        print(f"Processing file: {file_name}")

        if not file_path.exists():
            print(f"Skipped. reason=file_not_found path={file_path}")
            continue

        try:
            pdf_bytes = file_path.read_bytes()
        except OSError as exc:
            print(f"Skipped. reason=file_read_failed detail={exc}")
            continue

        parsed = parser.parse_file(
            pdf_bytes,
            filename=file_name,
            frontend_test_name=frontend_test_name,
        )

        report_type = parsed.get("type")
        extracted_data = parsed.get("data")
        error = parsed.get("error")
        ai_usage = parsed.get("ai_usage")

        if error or not extracted_data:
            print(f"Extraction failed. type={report_type} reason={error}")
            results.append(_build_result(file_name, report_type, extracted_data, None, error, ai_usage))
            continue

        extraction_method = extracted_data.get("extraction_method", "unknown")
        print(f"Extraction succeeded. type={report_type} method={extraction_method}")

        analysis = analyzer.analyze(str(report_type), extracted_data)
        if analysis:
            severity = analysis.get("severity", "unknown")
            if hasattr(severity, "value"):
                severity = severity.value
            print(f"Analysis succeeded. severity={severity}")
        else:
            print("Analysis skipped. reason=no_matching_analyzer")

        results.append(_build_result(file_name, report_type, extracted_data, analysis, None, ai_usage))

    print("=" * 72)
    print("Final integration payload:")
    payload = {
        "files": results,
        "batch_ai_usage": aggregate_ai_usage(results),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("Integration test suite finished.")


def _build_result(
    file_name: str,
    report_type: Any,
    extracted_data: Optional[Dict[str, Any]],
    analysis: Optional[Dict[str, Any]],
    error: Optional[str],
    ai_usage: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "file": file_name,
        "identified_type": report_type,
        "raw_data_extracted": extracted_data,
        "analysis_result": analysis,
        "error": error,
        "ai_usage": ai_usage,
    }


if __name__ == "__main__":
    run_integration_test()
