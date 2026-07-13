OXYGEN_SCHEMA = """
{
  "session": {
    "start_time": str | null,
    "end_time": str | null,
    "total_duration": str | null,
    "o2_score": int | null
  },
  "oxygen_summary": {"max": int | null, "avg": int | null, "min": int | null},
  "pulse_rate_summary": {"max": int | null, "avg": int | null, "min": int | null},
  "drops": {"over_4_percent": int | null, "over_3_percent": int | null},
  "oxygen_thresholds": [
    {"range_label": str, "duration": str | null, "percentage": str | null}
  ]
}
"""


def build_oxygen_vision_prompt() -> str:
    return f"""
You are a medical document extraction engine.
Extract oxygen saturation and pulse summary data from the provided report image.

Rules:
- Return only valid JSON.
- Use the exact structure from the schema.
- Use null when a value is not visible.
- Do not infer missing values.
- Keep durations and percentages as displayed.

Schema:
{OXYGEN_SCHEMA}
""".strip()
