ECG_SCHEMA = """
{
  "waveform_analysis": {
    "rhythm_regularity": str | null,
    "p_wave_visibility": str | null,
    "st_segment_status": str | null,
    "overall_visual_impression": str | null
  },
  "heart_rate_bpm": int | null
}
"""


def build_ecg_vision_prompt() -> str:
    return f"""
You are a medical document extraction engine for ECG reports.
Extract only visually supported ECG metrics from the provided report image.

Rules:
- Return only valid JSON.
- Extract heart_rate_bpm if visible.
- Summarize waveform fields only when visible or clearly stated.
- Do not provide diagnosis beyond the fields in the schema.
- Use null when a field is not visible.

Schema:
{ECG_SCHEMA}
""".strip()
