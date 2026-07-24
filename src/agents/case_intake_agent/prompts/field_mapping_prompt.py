# src/agents/case_intake_agent/prompts/field_mapping_prompt.py

import json


def create_field_mapping_prompt(
    field_manifest: dict,
    evidence: list,
    user_message: str,
) -> str:
    """
    Build prompt for mapping evidence to fields.
    """

    return f"""
You are a comprehensive legal information extraction system.

Your task is to extract and populate as much relevant, detailed, and accurate information as possible from the provided user message and evidence into fields defined in the field manifest.

FIELD MANIFEST:
{json.dumps(field_manifest, indent=2)}

EXTRACTED EVIDENCE:
{json.dumps(evidence, indent=2)}

USER MESSAGE:
{user_message}

RULES:

1. Extract all relevant details, facts, names, dates, amounts, descriptions, and context present in the evidence or user message.
2. ONLY use field names that already exist in the field manifest.
3. NEVER invent new field names.
4. If a value cannot be determined, do not include the field.
5. Return ONLY valid JSON.
6. Return key-value pairs only.
7. Dates should remain exactly as found.
8. Preserve names, addresses, vehicle numbers, phone numbers, IDs, monetary figures, and narrative details exactly and completely.

Example:

{{
    "petitioner_name": "Ramesh Kumar",
    "date_of_birth": "12/05/1990"
}}

Return JSON only.
"""