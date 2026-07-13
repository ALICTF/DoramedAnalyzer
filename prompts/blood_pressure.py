BLOOD_PRESSURE_SCHEMA = """
{
  "systolic_mmhg": int | null,
  "diastolic_mmhg": int | null,
  "pulse_bpm": int | null,
  "measurement_date": str | null
}
"""


def build_blood_pressure_vision_prompt() -> str:
    return f"""
You are a medical document extraction engine.
Extract the latest blood pressure record from the provided report image.

Rules:
- Return only valid JSON.
- Extract the latest visible systolic, diastolic, pulse, and measurement date.
- Use null when a value is not visible.
- Do not explain or add markdown.
- Blood pressure values must be in mmHg.

Schema:
{BLOOD_PRESSURE_SCHEMA}
""".strip()
