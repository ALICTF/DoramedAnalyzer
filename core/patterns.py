# core/patterns.py
import re
from typing import Dict, Tuple, Pattern, Callable, Any, Final

class PDFPatterns:


    PatternMapping = Dict[str, Tuple[Pattern, Callable[[str], Any]]]

    # ==========================================
    # 1. Body Composition (BC) Patterns
    # ==========================================
    BC_PATTERNS: Final[PatternMapping] = {
        "height_cm": (re.compile(r"Heigh?t?\s*[:\-]?\s*(\d+)\s*cm", re.IGNORECASE), int),
        "gender": (re.compile(r"(?:Gender\s*[:\-]?\s*)?(Male|Female)", re.IGNORECASE), str),
        "measurement_date": (re.compile(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"), str),
        "body_score": (re.compile(r"Body\s+score\s*[:\-]?\s*(\d+)", re.IGNORECASE), int),
        "weight_kg": (re.compile(r"Weight\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "skeletal_muscle_kg": (re.compile(r"Skeletal\s+muscle\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "fat_mass_kg": (re.compile(r"Fat\s+mass\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "bmi": (re.compile(r"BMI\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "body_fat_rate_percent": (re.compile(r"Body\s+fat\s+rate\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "obesity_percent": (re.compile(r"Obesity\s*[:\-]?\s*([\d\.]+)%", re.IGNORECASE), float),
        "weight_control_kg": (re.compile(r"Weight\s+control\s*[:\-]?\s*(-?[\d\.]+)kg", re.IGNORECASE), float),
        "fat_control_kg": (re.compile(r"Fat\s+control\s*[:\-]?\s*(-?[\d\.]+)kg", re.IGNORECASE), float),
        "muscle_control_kg": (re.compile(r"Muscle\s+control\s*[:\-]?\s*([\+\-]?[\d\.]+)kg", re.IGNORECASE), float),
        "bone_mass_kg": (re.compile(r"Bone\s+mass\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "protein_kg": (re.compile(r"Protein\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "body_water_kg": (re.compile(r"Body\s+water\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "muscle_kg": (re.compile(r"Muscle\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "visceral_fat_grade": (re.compile(r"Visceral\s+fat\s+grade\s*[:\-]?\s*(\d+)", re.IGNORECASE), int),
        "bmr_kcal": (re.compile(r"(?:Basal\s+metabolic\s+rate|BMR)\s*[:\-]?\s*(\d+)", re.IGNORECASE), int),
        "fat_free_body_weight_kg": (re.compile(r"Fat-free\s+body\s+weight\s*\(?kg\)?\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "subcutaneous_fat_percent": (re.compile(r"Subcutaneous\s+fat\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "smi": (re.compile(r"SMI\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE), float),
        "body_age": (re.compile(r"Body\s+age\s*[:\-]?\s*(\d+)", re.IGNORECASE), int),
    }

    # ==========================================
    # 2. Blood Pressure (BP) Patterns
    # ==========================================
    BP_PATTERNS: Final[PatternMapping] = {
        "user_name": (re.compile(r"Name\s*[:\-]?\s*(\w+)", re.IGNORECASE), str),
        "device": (re.compile(r"Device\s*[:\-]?\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE), str),
    }
    
    # Specific isolated patterns for BP that require multi-match or custom logic
    BP_DATE_PATTERN: Final[Pattern] = re.compile(r"(\d{1,2}\s\w{3}\s\d{4},\s*\d{2}:\d{2}\s[AP]\.?M\.?)", re.IGNORECASE)
    BP_MEASUREMENT_PATTERN: Final[Pattern] = re.compile(r"\b([6-9]\d|1\d{2}|2\d{2})\s*/\s*([3-9]\d|1\d{2})\b") 
    BP_PULSE_PATTERN: Final[Pattern] = re.compile(r"(\d{2,3})\s*bpm", re.IGNORECASE)

    # ==========================================
    # 3. Electrocardiogram (ECG) Patterns
    # ==========================================
    # Standard metadata patterns to assist the primary Vision API extraction
    ECG_PATTERNS: Final[PatternMapping] = {
        "patient_name": (re.compile(r"Name:\s*([a-zA-Z\s]+)", re.IGNORECASE), str),
        "heart_rate_bpm": (re.compile(r"HR:\s*\$?(\d+)\s*/min", re.IGNORECASE), int),
        "duration_sec": (re.compile(r"Measurement\s+time:\s*(\d+)\s*s", re.IGNORECASE), int),
    }

    # ==========================================
    # 4. Blood Oxygen (O2) Patterns
    # ==========================================
    # Standard metadata patterns to assist the primary Vision API extraction
    O2_PATTERNS: Final[PatternMapping] = {
        "patient_name": (re.compile(r"Name:\s*([a-zA-Z\s]+)", re.IGNORECASE), str),
        "duration": (re.compile(r"Duration\s+(\d{2}:\d{2})", re.IGNORECASE), str),
    }