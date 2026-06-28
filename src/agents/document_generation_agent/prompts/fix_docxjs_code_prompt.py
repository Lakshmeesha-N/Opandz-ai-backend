# src/agents/document_generation_agent/prompts/fix_docxjs_code_prompt.py

def create_fix_docxjs_code_prompt(
    generated_code: str,
    validation_error: str,
) -> str:

    return f"""
You are an expert DOCX.js engineer.

The previously generated DOCX.js code failed validation.

Your task is to repair the code.

RULES:

1. Fix only the issues necessary to resolve the validation error.
2. Preserve all existing functionality.
3. Preserve all function names.
4. Preserve buildDocument().
5. Preserve execution order.
6. Preserve document structure.
7. Preserve imports unless they are incorrect.
8. Preserve formatting logic.
9. Return complete corrected code.
10. Return JavaScript only.
11. No markdown.
12. No explanations.
13. No backticks.

VALIDATION ERROR:

{validation_error}

GENERATED CODE:

{generated_code}
"""