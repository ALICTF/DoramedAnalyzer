# Doramed Analyzer Backend Integration Guide

This file is the backend handoff document for the analyzer project. It explains how to configure the project, validate uploaded PDFs, extract report data, run health analysis, understand responses, and handle errors.

## What This Project Does

The project has two separate responsibilities:

1. PDF data collection with `PDFReportParser.parse_file(...)`
2. Health analysis with `HealthAnalyzer.analyze(...)`

You can use only the PDF parser if you only need extracted data. Use the analyzer only when you also need a health report such as severity, kind, message, and measured value.

## Important Files

| File | Purpose |
| --- | --- |
| `pdf_extractor.py` | Public import for `PDFReportParser`. |
| `services/pdf_report_parser.py` | Main PDF validation and extraction service. |
| `services/report_validation.py` | Validates uploaded filename/title against actual PDF content. |
| `validators/title_match.py` | Normalizes report names and compares title category to content category. |
| `services/health_analyzer.py` | Converts extracted values into health analysis output. |
| `core/settings.py` | Loads `.env` and environment settings. |
| `.env.example` | Safe example env file for coworkers. |
| `tests/` | Parser, validator, analyzer, settings, and integration tests. |

## Environment Setup

Copy the example env file:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
GAPGPT_API_KEY=your_real_gapgpt_api_key
GAPGPT_BASE_URL=https://api.gapgpt.app/v1
```

The real `.env` file must stay local. It is ignored by `.gitignore`.

The app loads `.env` automatically through `core.settings.get_settings()`. Existing machine environment variables override values from `.env`.

## Environment Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GAPGPT_API_KEY` | Recommended | None | Enables AI vision/classification fallback. Without it, text-only extraction still works when possible. |
| `GAPGPT_BASE_URL` | No | `https://api.gapgpt.app/v1` | OpenAI-compatible GapGPT endpoint. |
| `DSTAND_TEXT_MODEL` | No | `qwen3-235b-a22b` | Text classification model. |
| `DSTAND_VISION_MODEL` | No | `gemini-2.5-flash-lite` | Main vision model. |
| `DSTAND_VISION_FALLBACK_MODEL` | No | `gemini-3.1-flash-lite` | Vision fallback model. |
| `DSTAND_VISION_PREMIUM_MODEL` | No | `gemini-3.5-flash` | Premium vision model. |
| `DSTAND_MAX_VISION_PAGES` | No | `3` | Max pages for vision extraction. |
| `DSTAND_PDF_SAMPLE_PAGES` | No | `3` | Number of pages sampled for validation/classification. |
| `DSTAND_PDF_RENDER_DPI` | No | `150` | PDF render DPI for vision. |
| `DSTAND_OCR_DPI` | No | `200` | OCR render DPI. |
| `DSTAND_OCR_ENABLED` | No | `true` | Enables OCR fallback. |
| `DSTAND_LLM_TEMPERATURE` | No | `0.0` | LLM temperature. |
| `DSTAND_CLASSIFICATION_MIN_CONFIDENCE` | No | `0.6` | Minimum confidence for generic classification. |
| `DSTAND_LOG_LEVEL` | No | `INFO` | Application log level. |
| `DSTAND_MODEL_PRICING` | No | Built-in table | Optional usage-cost pricing override. |

## Backend Input Contract

The current backend has one filename field. There is no separate frontend test name.

Required input:

| Input | Type | Description |
| --- | --- | --- |
| `pdf_bytes` | `bytes` | Raw uploaded PDF bytes. |
| `filename` | `str` | Uploaded file name, for example `blood_pressure.pdf`. Used as validation title. |

`parse_file(...)` still has a legacy `frontend_test_name` argument, but the current backend should not send it.

## Recommended Main Flow

1. Receive uploaded PDF.
2. Read bytes.
3. Pass bytes and filename to `PDFReportParser.parse_file(...)`.
4. If `parsed["error"]` is not `None`, return an error response.
5. If parser succeeds and you need analysis, pass `parsed["type"]` and `parsed["data"]` to `HealthAnalyzer.analyze(...)`.

## Option A: Use Only PDF Data Collector

Use this when backend only needs validation and extracted PDF data.

```python
from pdf_extractor import PDFReportParser


def collect_pdf_data(uploaded_file):
    parser = PDFReportParser()

    return parser.parse_file(
        pdf_bytes=uploaded_file.read(),
        filename=uploaded_file.name,
    )
```

`parse_file(...)` returns:

```python
{
    "type": str,
    "filename": str,
    "data": dict | None,
    "error": str | None,
    "ai_usage": dict,
    "title_validation": dict,
}
```

## Option B: Use PDF Collector Plus Analyzer

Use this when backend needs both extracted data and a health report.

```python
from pdf_extractor import PDFReportParser
from analyzer import HealthAnalyzer


def handle_report_upload(uploaded_file):
    parser = PDFReportParser()
    analyzer = HealthAnalyzer()

    parsed = parser.parse_file(
        pdf_bytes=uploaded_file.read(),
        filename=uploaded_file.name,
    )

    if parsed["error"]:
        return {
            "ok": False,
            "status": "validation_error" if parsed["title_validation"]["status"] == "mismatch" else "parse_error",
            "message": parsed["error"],
            "pdf": parsed,
            "analysis": None,
        }

    analysis = analyzer.analyze(parsed["type"], parsed["data"])

    return {
        "ok": True,
        "status": "success",
        "message": "Report file was validated, parsed, and analyzed successfully.",
        "pdf": parsed,
        "analysis": analysis,
    }
```

## Validation Rules

Before parsing, the system validates the uploaded filename/title against the real PDF content.

Example:

| Uploaded filename | Actual file content | Result |
| --- | --- | --- |
| `blood_pressure.pdf` | Blood pressure report | Accepted |
| `blood_pressure.pdf` | Body composition report | Rejected |
| `damaged-file.pdf` | Unknown or unreadable | Not strictly rejected by validation, but parsing may fail |

Important: when `filename` is used as the title, the validator does not use that same filename to detect the content category. Content detection comes from PDF text or AI fallback. This prevents a wrongly named file from validating itself.

Validation statuses:

| Status | Meaning | Reject file? |
| --- | --- | --- |
| `match` | Filename/title category and content category are the same. | No |
| `mismatch` | Filename/title category and content category are different. | Yes |
| `unverified` | Filename/title or content could not be mapped confidently. | No |
| `skipped` | No filename/title was provided. | No |

## Supported Report Types

Dedicated parsers exist for:

```text
body_composition
blood_pressure
oxygen_level
ecg
```

Other medical documents can go through the generic parser when AI is configured.

## Supported Filename Examples

The title validator can understand common names like:

| Filename/title | Category |
| --- | --- |
| `blood_pressure.pdf` | `blood_pressure` |
| `blood-pressure-report.pdf` | `blood_pressure` |
| `body_composition.pdf` | `body_composition` |
| `body-composition.pdf` | `body_composition` |
| `inbody.pdf` | `body_composition` |
| `o2.pdf` | `oxygen_level` |
| `oxygen_report.pdf` | `oxygen_level` |
| `ecg.pdf` | `ecg` |
| `ekg.pdf` | `ecg` |

## Parser Success Response

This is the response when using only `parse_file(...)`.

```json
{
  "type": "blood_pressure",
  "filename": "blood_pressure.pdf",
  "data": {
    "systolic_mmhg": 123,
    "diastolic_mmhg": 66,
    "pulse_bpm": 72,
    "extraction_method": "text"
  },
  "error": null,
  "ai_usage": {
    "provider": "gapgpt",
    "used_ai": false,
    "summary": {
      "calls": 0,
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0
    },
    "calls": []
  },
  "title_validation": {
    "status": "match",
    "provided_title": "blood_pressure.pdf",
    "title_category": "blood_pressure",
    "content_category": "blood_pressure",
    "message": "The provided title matches the document content."
  }
}
```

## Parser Validation Error Response

```json
{
  "type": "blood_pressure.pdf",
  "filename": "blood_pressure.pdf",
  "data": null,
  "error": "File does not match its content: the provided title looks like 'blood_pressure' but the document content looks like 'body_composition'.",
  "ai_usage": {
    "provider": "gapgpt",
    "used_ai": false,
    "summary": {
      "calls": 0,
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0
    },
    "calls": []
  },
  "title_validation": {
    "status": "mismatch",
    "provided_title": "blood_pressure.pdf",
    "title_category": "blood_pressure",
    "content_category": "body_composition",
    "message": "File does not match its content: the provided title looks like 'blood_pressure' but the document content looks like 'body_composition'."
  }
}
```

## Parser Parse Error Response

This can happen when validation passes or is unverified, but text, vision, and OCR cannot extract valid data.

```json
{
  "type": "Unknown Medical Report",
  "filename": "damaged-file.pdf",
  "data": null,
  "error": "Text extraction failed and Vision API client is not configured.",
  "ai_usage": {
    "provider": "gapgpt",
    "used_ai": false,
    "summary": {
      "calls": 0,
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0
    },
    "calls": []
  },
  "title_validation": {
    "status": "unverified",
    "provided_title": "damaged-file.pdf",
    "title_category": null,
    "content_category": null,
    "message": "The provided title could not be mapped to a known category; skipping strict check."
  }
}
```

## Analyzer Usage

Only call analyzer after parser succeeds:

```python
analysis = analyzer.analyze(parsed["type"], parsed["data"])
```

Analyzer return shape:

```python
{
    "kind": str,
    "title": str,
    "message": str,
    "severity": str,
    "value": float,
    "unit": str,
    "metric": dict,
}
```

If the type is unsupported or required values are missing, analyzer returns `None`.

## Analyzer Examples

Blood pressure analysis:

```json
{
  "kind": "normal",
  "title": "Normal blood pressure",
  "message": "Blood pressure is in the healthy range.",
  "severity": "low",
  "value": 123.0,
  "unit": "mmHg",
  "metric": {
    "systolic_mmhg": 123,
    "diastolic_mmhg": 66,
    "pulse_bpm": 72,
    "formatted_bp": "123/66",
    "extraction_method": "text"
  }
}
```

Body composition analysis:

```json
{
  "kind": "healthy_weight",
  "title": "Healthy weight",
  "message": "BMI is in the healthy range.",
  "severity": "low",
  "value": 24.5,
  "unit": "kg/m^2",
  "metric": {
    "weight_kg": 80,
    "bmi": 24.5,
    "extraction_method": "text"
  }
}
```

Oxygen analysis:

```json
{
  "kind": "normal",
  "title": "Normal blood oxygen",
  "message": "Blood oxygen level is in the normal range.",
  "severity": "low",
  "value": 96.0,
  "unit": "%",
  "metric": {
    "oxygen_summary": {
      "min": 96,
      "avg": 97,
      "max": 98
    },
    "extraction_method": "text"
  }
}
```

ECG analysis:

```json
{
  "kind": "normal",
  "title": "Normal ECG",
  "message": "Heart rhythm and heart rate are normal.",
  "severity": "low",
  "value": 72.0,
  "unit": "bpm",
  "metric": {
    "heart_rate_bpm": 72,
    "waveform_analysis": {
      "rhythm_regularity": "regular"
    },
    "extraction_method": "text"
  }
}
```

Note: actual analyzer titles and messages come from `core/health_config.py`. Some current project strings are localized. Backend should depend on the keys and shape, not exact English text.

## Complete Backend Success Response

This is the recommended final API response when parser and analyzer both succeed.

```json
{
  "ok": true,
  "status": "success",
  "message": "Report file was validated, parsed, and analyzed successfully.",
  "pdf": {
    "type": "blood_pressure",
    "filename": "blood_pressure.pdf",
    "data": {
      "systolic_mmhg": 123,
      "diastolic_mmhg": 66,
      "pulse_bpm": 72,
      "formatted_bp": "123/66",
      "extraction_method": "text"
    },
    "error": null,
    "ai_usage": {
      "provider": "gapgpt",
      "used_ai": false,
      "summary": {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
      },
      "calls": []
    },
    "title_validation": {
      "status": "match",
      "provided_title": "blood_pressure.pdf",
      "title_category": "blood_pressure",
      "content_category": "blood_pressure",
      "message": "The provided title matches the document content."
    }
  },
  "analysis": {
    "kind": "normal",
    "title": "Normal blood pressure",
    "message": "Blood pressure is in the healthy range.",
    "severity": "low",
    "value": 123.0,
    "unit": "mmHg",
    "metric": {
      "systolic_mmhg": 123,
      "diastolic_mmhg": 66,
      "pulse_bpm": 72,
      "formatted_bp": "123/66",
      "extraction_method": "text"
    }
  },
  "meta": {
    "source": "pdf_upload",
    "validated": true,
    "parsed": true,
    "analyzed": true
  }
}
```

## Complete Backend Validation Error Response

```json
{
  "ok": false,
  "status": "validation_error",
  "message": "Uploaded filename does not match the file content.",
  "pdf": {
    "type": "blood_pressure.pdf",
    "filename": "blood_pressure.pdf",
    "data": null,
    "error": "File does not match its content: the provided title looks like 'blood_pressure' but the document content looks like 'body_composition'.",
    "ai_usage": {
      "provider": "gapgpt",
      "used_ai": false,
      "summary": {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
      },
      "calls": []
    },
    "title_validation": {
      "status": "mismatch",
      "provided_title": "blood_pressure.pdf",
      "title_category": "blood_pressure",
      "content_category": "body_composition",
      "message": "File does not match its content: the provided title looks like 'blood_pressure' but the document content looks like 'body_composition'."
    }
  },
  "analysis": null,
  "meta": {
    "source": "pdf_upload",
    "validated": false,
    "parsed": false,
    "analyzed": false
  }
}
```

## Complete Backend Parse Error Response

```json
{
  "ok": false,
  "status": "parse_error",
  "message": "Text extraction failed and Vision API client is not configured.",
  "pdf": {
    "type": "Unknown Medical Report",
    "filename": "damaged-file.pdf",
    "data": null,
    "error": "Text extraction failed and Vision API client is not configured.",
    "ai_usage": {
      "provider": "gapgpt",
      "used_ai": false,
      "summary": {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
      },
      "calls": []
    },
    "title_validation": {
      "status": "unverified",
      "provided_title": "damaged-file.pdf",
      "title_category": null,
      "content_category": null,
      "message": "The provided title could not be mapped to a known category; skipping strict check."
    }
  },
  "analysis": null,
  "meta": {
    "source": "pdf_upload",
    "validated": true,
    "parsed": false,
    "analyzed": false
  }
}
```

## Recommended HTTP Status Codes

| Case | Suggested HTTP status | Body status |
| --- | --- | --- |
| Parser and analyzer succeed | `200` | `success` |
| Parser succeeds, analyzer returns `None` | `200` | `success` or `analysis_unavailable` |
| Validation mismatch | `400` | `validation_error` |
| Unsupported/unreadable PDF | `422` | `parse_error` |
| Server exception outside parser | `500` | `server_error` |

## AI Usage Field

Every parser response includes `ai_usage`.

When no AI call is used:

```json
{
  "provider": "gapgpt",
  "used_ai": false,
  "summary": {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "calls": []
}
```

When AI is used, `used_ai` becomes `true`, `summary.calls` increases, and `calls` contains per-call usage details.

## Terminal Logs

Validation mismatch logs look like:

```text
ERROR dstand.ai.report_validation Report validation failed. file=blood_pressure.pdf provided_title='blood_pressure.pdf' title_category=blood_pressure content_category=body_composition reason=File does not match its content...
```

Parsing errors look like:

```text
ERROR dstand.ai.pdf_extractor Parse finished with error. file=damaged-file.pdf reason=Text extraction failed and Vision API client is not configured.
```

## Django Alert Helper

`services.health_analyzer.analyze_summary_result_helper(...)` is optional and only works inside the Django app environment where these models exist:

```python
apps.analyzer.models.TestFile
apps.analyzer.models.AlertKind
apps.analyzer.models.HealthAlert
```

If Django models are not available, the helper returns `None` and logs that Django integration is disabled.

Use this helper only when integrating with the Django alert system. For normal API usage, use `HealthAnalyzer.analyze(...)`.

## Local Testing

Run all tests:

```powershell
python -m pytest -q
```

Expected result at time of this guide:

```text
28 passed
```

Run the manual integration script:

```powershell
python test.py
```

If `GAPGPT_API_KEY` is missing, AI-powered fallback is disabled, but text extraction tests can still pass.

## Backend Checklist

Before deploying:

1. Create `.env` from `.env.example`.
2. Set `GAPGPT_API_KEY`.
3. Use `PDFReportParser()` without passing the key manually.
4. Pass only `pdf_bytes` and `filename` to `parse_file(...)`.
5. Stop immediately if `parsed["error"]` is present.
6. Call `HealthAnalyzer.analyze(...)` only after parser success.
7. Return `title_validation` to clients for debugging validation problems.
8. Keep `ai_usage` in logs or API response if token/cost tracking matters.
