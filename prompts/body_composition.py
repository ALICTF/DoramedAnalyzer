BODY_COMPOSITION_SCHEMA = """
{
  "height_cm": int | null,
  "weight_kg": float | null,
  "gender": str | null,
  "body_score": int | null,
  "fat_mass_kg": float | null,
  "bmi": float | null,
  "body_fat_rate_percent": float | null,
  "muscle_kg": float | null,
  "visceral_fat_grade": int | null,
  "bmr_kcal": int | null,
  "body_age": int | null,
  "protein_kg": float | null,
  "body_water_kg": float | null
}
"""


def build_body_composition_vision_prompt() -> str:
    return f"""
You are a medical document extraction engine.
Extract body composition metrics from the provided report image.

Rules:
- Return only valid JSON.
- Use the exact keys and value types from the schema.
- Use null when a value is not visible.
- Do not infer values that are not present, except BMI may be computed only when height and weight are both visible.
- Preserve medical units implied by the key names.

Schema:
{BODY_COMPOSITION_SCHEMA}
""".strip()
