def generate_field_manifest(document_text: str) -> str:
    """
    Takes plain document text.
    Returns a prompt asking LLM for a field manifest — flat list of variable fields.
    """

    prompt = f"""You are an expert legal document analyst.

Analyze this document text carefully and identify all variable fields that must be collected from evidence to generate a new version of this document.

DEFINITION OF VARIABLE FIELD:
A variable field is any value that changes per case — such as names, dates, amounts, locations, vehicle numbers, case numbers, ages, addresses, injury details etc.
Do NOT include fixed content like court names, legal boilerplate, section headings, or standard legal phrases.

RULES:
1. Read the actual content carefully
2. Identify only fields that would change for a new case
3. Each field must have a clear snake_case name and one-line description
4. Return ONLY raw valid JSON — no markdown, no backticks, no explanation, no preamble

DOCUMENT TEXT:
{document_text}

REQUIRED OUTPUT FORMAT:
{{
  "required_fields": [
    {{"field": "field_name", "description": "One to three line description of what to collect"}},
    {{"field": "field_name_2", "description": "One to three line description of what to collect"}}
  ]
}}"""

    return prompt