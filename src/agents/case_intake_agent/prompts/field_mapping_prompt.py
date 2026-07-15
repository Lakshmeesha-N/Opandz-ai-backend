# src/agents/case_intake_agent/prompts/field_mapping_prompt.py

import json


def create_field_mapping_prompt(
    field_manifest: dict,
    evidence: list,
    user_message: str,
    existing_important_information: list = None,
) -> str:
    """
    Build prompt for mapping evidence to fields.
    """

    existing_important_information = existing_important_information or []

    return f"""
You are a legal information extraction system.

Your task is to populate fields from the field manifest AND extract important case facts.

FIELD MANIFEST:
{json.dumps(field_manifest, indent=2)}

EXTRACTED EVIDENCE:
{json.dumps(evidence, indent=2)}

USER MESSAGE:
{user_message}

RULES:

1. ONLY use field names that already exist in the field manifest for required fields.
2. NEVER invent new field names for required fields.
3. If a required field value cannot be determined from the evidence or message, write it as a placeholder string: "[UNKNOWN - <field description>]". For example: "[UNKNOWN - petitioner date of birth]".
4. Always include every required field in your output — use a placeholder if the real value is missing.
5. Dates should remain exactly as found. Preserve names, addresses, vehicle numbers, phone numbers, IDs, etc.

IMPORTANT INFORMATION:

6. Also extract a list of important facts, observations, or context from the evidence and user message that are NOT captured by the required fields. These are things like key events, circumstances, admissions, witness details, insurance status, injuries, or anything a lawyer would want to remember.
7. Return these as a JSON array under the key "important_information". Each item must be a short, clear string (one fact per item).
8. Only include NEW facts not already present in the existing list below. Do not repeat existing items.
9. If there are no new important facts, return "important_information" as an empty list [].

EXISTING IMPORTANT INFORMATION (already captured, do not repeat):
{json.dumps(existing_important_information, indent=2)}

Output format — return ONLY valid JSON with all required fields plus important_information:

{{
    "petitioner_name": "Ramesh Kumar",
    "date_of_birth": "[UNKNOWN - petitioner date of birth]",
    "incident_date": "12/05/2023",
    "important_information": [
        "Vehicle was rear-ended at a traffic signal",
        "Witness present at the scene — name not yet provided",
        "Client states the vehicle was fully insured"
    ]
}}

Return JSON only.
"""