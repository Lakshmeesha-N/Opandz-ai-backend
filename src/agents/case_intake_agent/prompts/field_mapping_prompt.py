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
You are a legal information extraction system.

Your task is to populate fields from the field manifest.

FIELD MANIFEST:
{json.dumps(field_manifest, indent=2)}

EXTRACTED EVIDENCE:
{json.dumps(evidence, indent=2)}

USER MESSAGE:
{user_message}

RULES:

1. ONLY use field names that already exist in the field manifest.
2. NEVER invent new field names.
3. If a value cannot be determined, do not include the field.
4. Return ONLY valid JSON.
5. Return key-value pairs only.
6. Dates should remain exactly as found.
7. Preserve names, addresses, vehicle numbers, phone numbers, IDs, etc.

Example:

{{
    "petitioner_name": "Ramesh Kumar",
    "date_of_birth": "12/05/1990"
}}

Return JSON only.
"""