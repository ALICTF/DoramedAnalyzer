# Backend Integration Guide

This guide explains how backend services should validate uploaded report PDFs, extract report data, and run health analysis.

## Environment Setup

Copy the example env file and fill in the real API key:

```powershell
Copy-Item .env.example .env
```

```env
GAPGPT_API_KEY=your_real_gapgpt_api_key
GAPGPT_BASE_URL=https://api.gapgpt.app/v1
```

The app loads `.env` automatically through `core.settings.get_settings()`. Do not commit the real `.env` file.

## Main Flow

1. Receive PDF bytes from the uploaded file.
2. Receive the uploaded file name.
3. Call `PDFReportParser.parse_file(...)`.
4. If `error` is present, stop and return the parser response.
5. If extraction succeeds, call `HealthAnalyzer.analyze(...)`.

The backend currently has one file name field. The parser uses `filename` as the report title for validation. When `filename` is used as the title, the validator does not use that same filename to detect the file content category, so a wrongly named file cannot validate itself.

## Usage

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
            "pdf": parsed,
            "analysis": None,
        }

    analysis = analyzer.analyze(parsed["type"], parsed["data"])

    return {
        "ok": True,
        "status": "success",
        "pdf": parsed,
        "analysis": analysis,
    }
```

## Parser Response

Successful extraction:

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

Validation failure:

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

## Analyzer Response

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

## Complete Backend Success Response

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

## Validation Statuses

| Status | Meaning |
| --- | --- |
| `match` | Filename/title and content category are the same. |
| `mismatch` | Filename/title and content category are different. File is rejected. |
| `unverified` | Filename/title or content could not be mapped confidently. File is not rejected. |
| `skipped` | No filename/title was provided. File is not rejected. |

## Supported Analyzer Types

```text
body_composition
blood_pressure
oxygen_level
ecg
```

## Testing

```powershell
python -m pytest -q
```
