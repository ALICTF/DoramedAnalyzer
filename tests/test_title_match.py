from validators.title_match import (
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_SKIPPED,
    STATUS_UNVERIFIED,
    check_title_matches_content,
    normalize_category,
)


def test_normalize_canonical_keys():
    assert normalize_category("blood_pressure") == "blood_pressure"
    assert normalize_category("ecg") == "ecg"


def test_normalize_free_form_titles():
    assert normalize_category("Blood Pressure Report") == "blood_pressure"
    assert normalize_category("InBody Body Composition") == "body_composition"
    assert normalize_category("SpO2 / Oxygen Level") == "oxygen_level"
    assert normalize_category("نوار قلب") == "ecg"


def test_normalize_uploaded_filenames():
    assert normalize_category("blood_pressure.pdf") == "blood_pressure"
    assert normalize_category("body-composition.pdf") == "body_composition"
    assert normalize_category("o2.pdf") == "oxygen_level"


def test_normalize_unknown_title_is_none():
    assert normalize_category("Complete Blood Count (CBC)") is None
    assert normalize_category("") is None
    assert normalize_category(None) is None


def test_match_when_title_and_content_agree():
    result = check_title_matches_content("Blood Pressure", "blood_pressure")
    assert result.status == STATUS_MATCH
    assert not result.is_mismatch


def test_mismatch_when_title_and_content_disagree():
    result = check_title_matches_content("Blood Pressure Report", "oxygen_level")
    assert result.status == STATUS_MISMATCH
    assert result.is_mismatch
    assert "does not match its content" in result.message


def test_unverified_when_content_unknown():
    result = check_title_matches_content("Blood Pressure", "unknown")
    assert result.status == STATUS_UNVERIFIED
    assert not result.is_mismatch


def test_unverified_when_title_not_categorizable():
    result = check_title_matches_content("Complete Blood Count", "blood_pressure")
    assert result.status == STATUS_UNVERIFIED
    assert not result.is_mismatch


def test_skipped_when_no_title():
    result = check_title_matches_content(None, "blood_pressure")
    assert result.status == STATUS_SKIPPED
    assert not result.is_mismatch
