from typing import Any, Dict, Optional


def is_valid_body_composition(data: Optional[Dict[str, Any]]) -> bool:
    if not data or "weight_kg" not in data:
        return False

    weight = data.get("weight_kg")
    if not _is_number_in_range(weight, 20, 350):
        return False

    bmi = data.get("bmi")
    if bmi is not None and not _is_number_in_range(bmi, 8, 100):
        return False

    return True


def is_valid_blood_pressure(data: Optional[Dict[str, Any]]) -> bool:
    if not data or "systolic_mmhg" not in data:
        return False

    systolic = data.get("systolic_mmhg")
    diastolic = data.get("diastolic_mmhg")
    if not _is_number_in_range(systolic, 60, 260):
        return False
    if not _is_number_in_range(diastolic, 30, 160):
        return False
    if float(diastolic) >= float(systolic):
        return False

    return True


def is_valid_oxygen(data: Optional[Dict[str, Any]]) -> bool:
    if not data or "oxygen_summary" not in data:
        return False

    summary = data.get("oxygen_summary") or {}
    values = [summary.get(key) for key in ("min", "avg", "max") if summary.get(key) is not None]
    if not values:
        return False
    if any(not _is_number_in_range(value, 0, 100) for value in values):
        return False
    if all(summary.get(key) is not None for key in ("min", "avg", "max")):
        if not float(summary["min"]) <= float(summary["avg"]) <= float(summary["max"]):
            return False

    return True


def is_valid_ecg(data: Optional[Dict[str, Any]]) -> bool:
    if not data or "heart_rate_bpm" not in data:
        return False

    return _is_number_in_range(data.get("heart_rate_bpm"), 20, 250)


def _is_number_in_range(value: Any, minimum: float, maximum: float) -> bool:
    return isinstance(value, (int, float)) and minimum <= float(value) <= maximum
