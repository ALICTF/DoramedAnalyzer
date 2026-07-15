from dataclasses import dataclass
from typing import Optional


OXYGEN_LEVEL = "oxygen_level"
ECG = "ecg"
BLOOD_PRESSURE = "blood_pressure"
BODY_COMPOSITION = "body_composition"

CANONICAL_CATEGORIES = (OXYGEN_LEVEL, ECG, BLOOD_PRESSURE, BODY_COMPOSITION)

_CATEGORY_KEYWORDS = {
    OXYGEN_LEVEL: ("oxygen", "o2", "spo2", "اکسیژن"),
    ECG: ("ecg", "ekg", "electrocardio", "نوار قلب"),
    BLOOD_PRESSURE: (
        "blood pressure",
        "systolic",
        "diastolic",
        "mmhg",
        "فشار خون",
        "فشار",
    ),
    BODY_COMPOSITION: (
        "body composition",
        "body analysis",
        "inbody",
        "composition",
        "آنالیز بدن",
        "bmi",
    ),
}


def normalize_category(name: Optional[str]) -> Optional[str]:
    if not name:
        return None

    raw_text = name.strip().lower()
    if not raw_text:
        return None

    if raw_text in CANONICAL_CATEGORIES:
        return raw_text

    text = raw_text.replace("_", " ").replace("-", " ").replace(".", " ")

    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return None


STATUS_MATCH = "match"
STATUS_MISMATCH = "mismatch"
STATUS_UNVERIFIED = "unverified"
STATUS_SKIPPED = "skipped"


@dataclass(frozen=True)
class TitleValidation:
    status: str
    provided_title: Optional[str]
    title_category: Optional[str]
    content_category: Optional[str]
    message: str

    @property
    def is_mismatch(self) -> bool:
        return self.status == STATUS_MISMATCH

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "provided_title": self.provided_title,
            "title_category": self.title_category,
            "content_category": self.content_category,
            "message": self.message,
        }


def check_title_matches_content(
    provided_title: Optional[str],
    content_category: Optional[str],
) -> TitleValidation:
    if not provided_title or not provided_title.strip():
        return TitleValidation(
            status=STATUS_SKIPPED,
            provided_title=provided_title,
            title_category=None,
            content_category=content_category,
            message="No title was provided by the caller; nothing to validate.",
        )

    title_category = normalize_category(provided_title)

    if title_category is None:
        return TitleValidation(
            status=STATUS_UNVERIFIED,
            provided_title=provided_title,
            title_category=None,
            content_category=content_category,
            message="The provided title could not be mapped to a known category; skipping strict check.",
        )

    if not content_category or content_category == "unknown":
        return TitleValidation(
            status=STATUS_UNVERIFIED,
            provided_title=provided_title,
            title_category=title_category,
            content_category=content_category,
            message="The document content could not be categorized; unable to verify the title.",
        )

    if title_category == content_category:
        return TitleValidation(
            status=STATUS_MATCH,
            provided_title=provided_title,
            title_category=title_category,
            content_category=content_category,
            message="The provided title matches the document content.",
        )

    return TitleValidation(
        status=STATUS_MISMATCH,
        provided_title=provided_title,
        title_category=title_category,
        content_category=content_category,
        message=(
            "File does not match its content: the provided title looks like "
            f"'{title_category}' but the document content looks like '{content_category}'."
        ),
    )
