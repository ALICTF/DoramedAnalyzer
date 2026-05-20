# Doramed Health Report Analyzer

This project is a smart, automated Python-based tool designed to extract, identify, and analyze medical data from health report PDFs (such as Body Composition/InBody reports and Blood Pressure logs). Using Regular Expressions (Regex) and PDF processing libraries, the project extracts vital metrics and provides structured clinical analysis alongside localized Persian health recommendations based on standard medical benchmarks.

## 🚀 Key Features
- **Automated Report Type Identification:** Intelligently detects whether an incoming file is a Blood Pressure or a Body Composition (InBody) report based on both the filename and its textual content.
- **Advanced PDF Parser (`pdf_extractor.py`):** Accurately extracts critical health indicators including BMI, Fat Mass, Skeletal Muscle Mass, Systolic/Diastolic blood pressure, Pulse Rate, and automatically computes Mean Arterial Pressure (MAP).
- **Health Analysis Engine (`analyzer.py`):** Evaluates extracted data metrics and categorizes them into structured risk tiers (`low`, `medium`, `high`, `critical`).
- **Flexible Configuration & Localization (`config.py`):** Centralizes medical thresholds, risk levels, and localized Persian feedback messages for easy maintenance.

---

## 📂 Project Structure (Project Tree)

```text
.
├── analyzer.py          # Core logic for health data analysis and insights
├── config.py            # Configuration file containing medical thresholds and Persian messages
├── pdf_extractor.py     # Handles PDF text extraction and Regex pattern parsing
├── main_test.py         # Test script to execute the end-to-end extraction and analysis pipeline
├── final_output.json    # Sample structured output generated from running the pipeline
├── sample_body.pdf      # Sample Body Composition report for testing
├── sample_bp.pdf        # Sample Blood Pressure report for testing
└── __init__.py          # Python package initialization file
```

---

## 🛠 Prerequisites & Installation

To run this project, you need Python 3.8 or higher. The only external dependency required is the `PyMuPDF` library (installed as `fitz`).

### Installing Dependencies
Run the following command in your terminal to install the required package:

```bash
pip install pymupdf
```

---

## 💻 Usage and Execution

To test the project and see the extraction pipeline in action using the default sample files, simply execute the main test script:

```bash
python main_test.py
```

### Code Example for Integration
You can easily import and utilize the modules of this project within your own services or back-end pipelines:

```python
from pdf_extractor import PDFReportParser
from analyzer import HealthAnalyzer

# 1. Read the PDF file as bytes
with open("sample_bp.pdf", "rb") as f:
    pdf_bytes = f.read()

# 2. Extract data from the PDF
parser = PDFReportParser()
extracted_data = parser.parse_file(pdf_bytes, "sample_bp.pdf")

# 3. Analyze the extracted metrics
if "error" not in extracted_data:
    analyzer = HealthAnalyzer()
    analysis_result = analyzer.analyze(extracted_data['type'], extracted_data['data'])
    print(analysis_result)
```

---

## 📊 Sample Output (Structured JSON)

Upon successful execution, the pipeline generates a structured list of dictionaries (or a JSON file) containing both the raw extracted parameters and the clinical analysis:

```json
[
  {
    "file": "body_report.pdf",
    "raw_data": {
      "height_cm": 175,
      "weight_kg": 78.5,
      "bmi": 25.6,
      "body_fat_rate_percent": 22.4
    },
    "analysis": {
      "kind": "over_weight",
      "title": "اضافه وزن",
      "message": "شاخص توده بدنی شما در محدوده «اضافه وزن» قرار دارد. ۳۰ دقیقه پیاده‌روی روزانه توصیه می‌شود.",
      "severity": "high",
      "value": 25.6,
      "unit": "kg/m²",
      "metric": { "bmi": 25.6 }
    }
  }
]
```

---

## ⚙️ Customizing Thresholds and Messages

All clinical numerical benchmarks (such as hypertensive crisis limits or BMI brackets) along with the localized Persian response texts are decoupled into `config.py`. If you need to adjust medical metrics based on updated guidelines or change the wording of the advice, you can modify the following fields inside `HealthConfig`:

- `BMI_THRESHOLDS`: Cut-off points for underweight, overweight, and obesity classifications.
- `BMI_MESSAGES`: Headings, clinical advice text, and severity rankings (`low` to `critical`) for each weight class.
- `BP_THRESHOLDS`: Systolic and Diastolic ranges for Hypotension, Normal, Elevated, Stage 1, Stage 2, and Hypertensive Crisis.
- `BP_MESSAGES`: Risk alerts and recommended actions corresponding to the user's blood pressure classification.

---

## 👥 Contributing

This project is actively maintained across two separate repositories:
- **Personal Repository:** [ALICTF/DoramedAnalyzer](https://github.com/ALICTF/DoramedAnalyzer)
- **Company Repository:** [doramed-co/doramed_analyzer](https://github.com/doramed-co/doramed_analyzer)

If you wish to optimize text extraction (Regex Patterns) or add support for new health reports (e.g., Blood Test/Lab results), please submit a Pull Request or open an issue on GitHub.
```