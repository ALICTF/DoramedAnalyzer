from typing import Final


CLASSIFICATION_PROMPT: Final[str] = """
You are a medical document classification engine.
Classify the provided medical document before extraction.

The document may be any medical file, for example:
- laboratory report
- radiology report
- MRI, CT, ultrasound, X-ray, dental OPG, ECG, blood pressure, oxygen report
- prescription, discharge summary, pathology report, body composition report
- any other medical document

Return only valid JSON with this schema:
{
  "document_type": str,
  "modality": str | null,
  "body_region": str | null,
  "specialty": str | null,
  "language": str | null,
  "is_medical": bool,
  "confidence": float,
  "reason": str
}

Rules:
- document_type must be concise and human-readable, such as "Complete Blood Count", "Dental OPG", "Brain MRI", "Chest X-Ray", "Prescription", "Unknown Medical Document".
- confidence must be between 0 and 1.
- reason must be one short sentence based on visible evidence.
- Do not extract detailed medical results in this step.
""".strip()


TEXT_EXTRACTION_PROMPT: Final[str] = """
You are a medical document extraction engine.
The document has been classified as: {document_type}
Modality: {modality}
Body region: {body_region}
Specialty: {specialty}

Extract all clinically relevant information from the raw text below.

Rules:
- Return only valid JSON.
- Preserve the original meaning and medical units.
- Convert numeric values to int or float when safe.
- Use arrays for repeated tables, measurements, or observations.
- Use null only when a field is expected but not present.
- Do not invent values.
- Do not provide medical advice.
- Include patient/report metadata only if present.

Raw text:
{text}
""".strip()


VISION_EXTRACTION_PROMPT: Final[str] = """
You are a medical document extraction engine.
The document has been classified as: {document_type}
Modality: {modality}
Body region: {body_region}
Specialty: {specialty}

Extract all clinically relevant visible information from the provided image.

Rules:
- Return only valid JSON.
- Preserve all visible medical values, units, tables, findings, impressions, dates, and patient/report metadata.
- Use arrays for repeated rows, measurements, findings, teeth, anatomical regions, or lab tests.
- For imaging documents such as MRI, CT, X-Ray, ultrasound, or dental OPG, extract findings, impression, anatomy, laterality, modality, and visible measurements.
- For lab documents, extract test name, result, unit, reference range, and flags when visible.
- Do not infer hidden or unreadable values.
- Do not provide medical advice.
""".strip()


def build_classification_text_prompt(text: str, filename: str) -> str:
    return f"{CLASSIFICATION_PROMPT}\n\nFilename: {filename or 'unknown'}\nRaw text sample:\n{text[:6000]}"


def build_classification_vision_prompt(filename: str) -> str:
    return f"{CLASSIFICATION_PROMPT}\n\nFilename: {filename or 'unknown'}"


def build_generic_text_prompt(
    *,
    document_type: str,
    modality: str | None,
    body_region: str | None,
    specialty: str | None,
    text: str,
) -> str:
    return TEXT_EXTRACTION_PROMPT.format(
        document_type=document_type,
        modality=modality,
        body_region=body_region,
        specialty=specialty,
        text=text,
    )


def build_generic_vision_prompt(
    *,
    document_type: str,
    modality: str | None,
    body_region: str | None,
    specialty: str | None,
) -> str:
    return VISION_EXTRACTION_PROMPT.format(
        document_type=document_type,
        modality=modality,
        body_region=body_region,
        specialty=specialty,
    )
