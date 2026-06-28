# src/agents/document_generation_agent/helpers/create_docxjs_generation_prompt.py

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)


def create_docxjs_generation_prompt(
    state: AgentState,
) -> str:

    return f"""
You are an expert DOCX.js engineer and document rendering architect.

Your task is to generate production-ready DOCX.js code from the provided blueprint, document configuration, and case data.

==================================================================
INPUTS PROVIDED
==================================================================

1. case_data
2. document_config
3. blueprint

==================================================================
GOAL
==================================================================

Generate a complete DOCX.js implementation that can recreate the entire document.

The generated code must contain:

1. One function for every header_group.
2. One function for every semantic_group.
3. One function for every footer_group.
4. One final buildDocument() function that assembles the document.

==================================================================
FUNCTION NAMING RULES
==================================================================

Header:

section_header
↓

build_section_header()

Semantic Group:

01_document_title_and_summary
↓

build_01_document_title_and_summary()

02_ai_fundamentals
↓

build_02_ai_fundamentals()

Footer:

section_footer
↓

build_section_footer()

Use the exact semantic group names when creating function names.

==================================================================
SECTION HANDLING RULES
==================================================================

1. document_config may contain multiple sections.
2. Handle all sections.
3. Respect section boundaries.
4. Respect execution order.
5. Respect section metadata.
6. Respect page dimensions.
7. Respect margins.
8. Respect section-specific formatting.
9. Respect block ordering.

==================================================================
BLUEPRINT RULES
==================================================================

1. Preserve header blocks.
2. Preserve body blocks.
3. Preserve footer blocks.
4. Preserve headings.
5. Preserve paragraphs.
6. Preserve tables.
7. Preserve spacing.
8. Preserve alignment.
9. Preserve indentation.
10. Preserve styles.
11. Preserve run-level formatting.
12. Preserve bold formatting.
13. Preserve italic formatting.
14. Preserve colors.
15. Preserve font sizes.
16. Preserve table structures.
17. Preserve editable metadata.
18. Preserve ordering.

==================================================================
CASE DATA RULES
==================================================================

1. Use case_data whenever dynamic values exist.
2. Replace placeholders with case_data values.
3. Do not hardcode dynamic values.
4. Safely handle missing values.

==================================================================
DOCX.JS RULES
==================================================================

1. Use DOCX.js constructs only.
2. Generate valid JavaScript.
3. Generate production-ready code.
4. Include all required DOCX.js imports.
5. Export every generated function.
6. Every function must return valid DOCX.js elements.
7. Avoid duplicate code whenever possible.
8. Avoid circular dependencies.
9. Ensure functions can be reused independently.
10. Ensure generated code can be assembled later.

==================================================================
ASSEMBLY RULES
==================================================================

Generate:

export function buildDocument(caseData)

This function must:

1. Create document sections.
2. Call all generated functions.
3. Preserve execution order.
4. Preserve section ordering.
5. Preserve header/footer ordering.
6. Return a complete DOCX.js document.
7. Return:

   new Document({...})

8. The returned Document must be directly executable without modification.
9. The returned Document must support DOCX export.
10. The returned Document must support real-time preview rendering.
==================================================================
VALIDATION RULES
==================================================================

The generated code MUST:

1. Compile successfully.
2. Execute without syntax errors.
3. Execute without runtime errors.
4. Be importable.
5. Be exportable.
6. Be production ready.
7. Support future insertion of additional semantic groups.
8. Support future insertion of additional sections.

==================================================================
OUTPUT RULES
==================================================================

1. Return JavaScript code only.
2. Do not return markdown.
3. Do not return explanations.
4. Do not return comments.
5. Do not use backticks.
6. Do not describe the code.
7. Return only executable DOCX.js code.

==================================================================
CASE DATA
==================================================================

{state["case_data"]}

==================================================================
DOCUMENT CONFIG
==================================================================

{state["document_config"]}

==================================================================
BLUEPRINT
==================================================================

{state["blueprint"]}
"""