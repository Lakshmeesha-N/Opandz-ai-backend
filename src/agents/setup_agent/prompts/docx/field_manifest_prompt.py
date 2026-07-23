def generate_field_manifest(document_text: str) -> str:
    """
    Takes clean document markdown.
    Returns a prompt asking LLM for a field manifest dictionary mapping variable field names to descriptions.
    """

    prompt = f"""You are an expert document analyst.

Analyze this document markdown carefully and identify ALL variable fields that must be collected from the user or evidence to reconstruct/generate a new instance of this document.

DEFINITION OF VARIABLE FIELD:
A variable field is any value or content that changes per instance — including names, dates, amounts, locations, reference numbers, addresses, as well as detailed narrative descriptions (e.g. description of incident, background facts, specific claims, custom clauses, etc.).
Do NOT include fixed legal boilerplate, standard legal section headers, or invariant template framing text.

RULES:
1. Read the document content carefully.
2. Identify all variable fields needed to fully construct the document.
3. For each field, provide:
   - `field_name`: A clear, descriptive identifier in `snake_case` (e.g. `client_full_name`, `description_of_incident`, `incident_date`).
   - `description`: A clear, helpful explanation of what information or narrative details to collect for this field.
4. Return ONLY raw valid JSON — no markdown code block fences, no backticks, no explanatory text before or after.

DOCUMENT MARKDOWN:
{document_text}

REQUIRED OUTPUT FORMAT:
{{
  "fields": [
    {{
      "field_name": "client_full_name",
      "description": "Full legal name of the client"
    }},
    {{
      "field_name": "description_of_incident",
      "description": "Detailed narrative description of the incident, sequence of events, and facts"
    }}
  ]
}}"""

    return prompt