from validators import (
    is_valid_blood_pressure,
    is_valid_body_composition,
    is_valid_ecg,
    is_valid_oxygen,
)


def test_body_composition_range_validation():
    assert is_valid_body_composition({"weight_kg": 80, "bmi": 24.5})
    assert not is_valid_body_composition({"weight_kg": 800})


def test_blood_pressure_range_validation():
    assert is_valid_blood_pressure({"systolic_mmhg": 123, "diastolic_mmhg": 66})
    assert not is_valid_blood_pressure({"systolic_mmhg": 80, "diastolic_mmhg": 90})


def test_oxygen_range_validation():
    assert is_valid_oxygen({"oxygen_summary": {"min": 93, "avg": 96, "max": 97}})
    assert not is_valid_oxygen({"oxygen_summary": {"min": 98, "avg": 96, "max": 97}})


def test_ecg_range_validation():
    assert is_valid_ecg({"heart_rate_bpm": 68})
    assert not is_valid_ecg({"heart_rate_bpm": 400})
