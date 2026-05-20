import fitz
import logging
import re
from typing import Dict, Any, Tuple, Pattern, Optional

logger = logging.getLogger("dstand.ai.pdf_extractor")

class PDFPatterns:
    
    BC_PATTERNS = {
        "height_cm": (re.compile(r"Heigh?t?\s*[:]?\s*(\d+)\s*cm", re.I), int),
        "gender": (re.compile(r"(Male|Female)", re.I), str),
        "measurement_date": (re.compile(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"), str),
        "body_score": (re.compile(r"Body score\s*[:]?\s*(\d+)", re.I), int),
        "weight_kg": (re.compile(r"Weight\(kg\)\s*([\d\.]+)", re.I), float),
        "skeletal_muscle_kg": (re.compile(r"Skeletal muscle\(kg\)\s*([\d\.]+)", re.I), float),
        "fat_mass_kg": (re.compile(r"Fat mass\(kg\)\s*([\d\.]+)", re.I), float),
        "bmi": (re.compile(r"BMI.*?([\d\.]+)", re.I), float),
        "body_fat_rate_percent": (re.compile(r"Body fat rate.*?([\d\.]+)", re.I), float),
        "obesity_percent": (re.compile(r"Obesity.*?([\d\.]+)%", re.I), float),
        "weight_control_kg": (re.compile(r"Weight control\s*(-?[\d\.]+)kg", re.I), float),
        "fat_control_kg": (re.compile(r"Fat control\s*(-?[\d\.]+)kg", re.I), float),
        "muscle_control_kg": (re.compile(r"Muscle control\s*([\+\-]?[\d\.]+)kg", re.I), float),
        "bone_mass_kg": (re.compile(r"Bone mass\s*([\d\.]+)", re.I), float),
        "protein_kg": (re.compile(r"Protein\s*([\d\.]+)", re.I), float),
        "body_water_kg": (re.compile(r"Body water\s*([\d\.]+)", re.I), float),
        "muscle_kg": (re.compile(r"Muscle\s*([\d\.]+)", re.I), float),
        "visceral_fat_grade": (re.compile(r"Visceral fat grade\s*(\d+)", re.I), int),
        "bmr_kcal": (re.compile(r"Basal metabolic rate\s*(\d+)", re.I), int),
        "fat_free_body_weight_kg": (re.compile(r"Fat-free body weight\s*([\d\.]+)", re.I), float),
        "subcutaneous_fat_percent": (re.compile(r"Subcutaneous fat\s*([\d\.]+)", re.I), float),
        "smi": (re.compile(r"SMI\s*([\d\.]+)", re.I), float),
        "body_age": (re.compile(r"Body age\s*(\d+)", re.I), int),
    }

    BP_PATTERNS = {
        "user_name": (re.compile(r"Name:\s*(\w+)", re.I), str),
        "device": (re.compile(r"Device:\s*(.+)", re.I), str),
    }
    
    BP_DATE_PATTERN = re.compile(r"(\d{1,2}\s\w{3}\s\d{4},\s*\d{2}:\d{2}\s[AP]\.?M\.?)", re.I)
    BP_MEASUREMENT_PATTERN = re.compile(r"\b([6-9]\d|1\d{2}|2\d{2})\s*/\s*([3-9]\d|1\d{2})\b") 
    BP_PULSE_PATTERN = re.compile(r"(\d{2,3})\s*bpm", re.I)

class PDFReportParser:
    def __init__(self):
        self.patterns = PDFPatterns()

    def _extract_text(self, pdf_bytes: bytes) -> str:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                text = "\n".join(page.get_text("text") for page in doc)
            return text if text.strip() else ""
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return ""

    def _identify_type(self, text: str, filename: str) -> str:
        text_lower = text.lower()
        fname_lower = filename.lower()
        scores = {"body_composition": 0, "blood_pressure": 0}

        if any(k in fname_lower for k in ["body", "composition", "inbody"]): scores["body_composition"] += 2
        if any(k in fname_lower for k in ["blood", "pressure", "bp"]): scores["blood_pressure"] += 2

        if any(k in text_lower for k in ["fat mass", "smm", "visceral fat", "آنالیز بدن"]): scores["body_composition"] += 1
        if any(k in text_lower for k in ["sys", "dia", "mmhg", "فشار خون"]): scores["blood_pressure"] += 1

        if scores["body_composition"] > scores["blood_pressure"]: return "body_composition"
        if scores["blood_pressure"] > scores["body_composition"]: return "blood_pressure"
        return "unknown"

    def _apply_patterns(self, text: str, pattern_dict: Dict[str, Tuple[Pattern, type]]) -> Dict[str, Any]:
        data = {}
        for key, (pattern, cast_type) in pattern_dict.items():
            match = pattern.search(text)
            if match:
                try:
                    val = match.group(1).replace(",", "").strip()
                    data[key] = cast_type(val)
                except (ValueError, IndexError):
                    continue
        return data

    def _parse_body_composition(self, text: str) -> Dict[str, Any]:
        data = self._apply_patterns(text, self.patterns.BC_PATTERNS)
        
        if "bmi" not in data and "weight_kg" in data and "height_cm" in data:
            try:
                h_m = data["height_cm"] / 100.0
                w_kg = data["weight_kg"]
                calculated_bmi = round(w_kg / (h_m ** 2), 1)
                data["bmi"] = calculated_bmi
            except ZeroDivisionError:
                pass

        if not data or "weight_kg" not in data:
            return {"error": "No valid body composition data found."}
        return data

    def _parse_blood_pressure(self, text: str) -> Dict[str, Any]:
        data = self._apply_patterns(text, self.patterns.BP_PATTERNS)
        
        date_match = self.patterns.BP_DATE_PATTERN.search(text)
        bp_match = self.patterns.BP_MEASUREMENT_PATTERN.search(text)
        pulse_match = self.patterns.BP_PULSE_PATTERN.search(text)

        if bp_match:
            try:
                if date_match:
                    data["measurement_date"] = date_match.group(1)
                
                data["systolic_mmhg"] = int(bp_match.group(1))
                data["diastolic_mmhg"] = int(bp_match.group(2))
                
                if pulse_match:
                    data["pulse_bpm"] = int(pulse_match.group(1))
                
                data["map_mmhg"] = int(data["diastolic_mmhg"] + (1/3 * (data["systolic_mmhg"] - data["diastolic_mmhg"])))
                
            except ValueError as e:
                logger.error(f"Error casting BP values: {e}")

        if "systolic_mmhg" not in data:
            return {"error": "No valid blood pressure record found."}

        return data

    def parse_file(self, pdf_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        text = self._extract_text(pdf_bytes)
        if not text:
            return {"type": "unknown", "filename": filename, "error": "Empty text"}

        report_type = self._identify_type(text, filename)
        result = {"type": report_type, "filename": filename, "data": {}}
        
        if report_type == "body_composition":
            result["data"] = self._parse_body_composition(text)
        elif report_type == "blood_pressure":
            result["data"] = self._parse_blood_pressure(text)
        else:
            result["error"] = "Unknown report type"

        return result