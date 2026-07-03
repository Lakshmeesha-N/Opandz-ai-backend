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

Every one of these functions is fully self-contained and takes zero
parameters. See FUNCTION SIGNATURE RULES below.

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
FUNCTION SIGNATURE RULES
==================================================================

1. Every function — every header function, every footer function,
   every semantic_group function, and buildDocument — is defined
   with ZERO parameters. No exceptions.
2. No function signature may include caseData, data, params, or any
   other parameter name, under any circumstance.
3. All content a function needs is written directly inside that
   function as fully resolved literal text. Nothing is passed in
   from outside and nothing is read from an external variable.
4. buildDocument() itself takes no parameters and calls every other
   function with no arguments (e.g. build_03_suspension_details(),
   not build_03_suspension_details(caseData)).
5. If a function currently under construction would only make sense
   with a parameter, that is a signal the value it needs must
   instead be resolved now and hardcoded directly into that
   function's literal text — not solved by adding a parameter.

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
CONTENT & VALUE RULES
==================================================================

1. case_data, document_config, and blueprint are provided to you
   below as the fully resolved source of truth for THIS one
   document. You are not writing a reusable template — you are
   generating the final, finished code for this specific document
   instance.
2. Wherever the document's content depends on a value from
   case_data (a name, date, title, amount, ID, reason, etc.), write
   that ACTUAL value directly into the JS as literal text at
   generation time. Do not write caseData.<field>, do not use a
   template-literal variable, do not read the value from any
   argument — type the real resolved value straight into the string.
3. Do NOT invent, guess, or fabricate any value that is not present
   in case_data.
4. Do NOT emit generic placeholder text such as "[Employee Name]",
   "{{start_date}}", "TBD", "Insert value here", "N/A — pending", or
   similar. Every sentence must read as a finished, real document
   with real resolved content — never a template.
5. If the document is narrative or static in nature (a story, essay,
   article, or fixed report where case_data does not apply), write
   the real, finished content directly as literal text. The same
   zero-parameter rule applies — this is not an exception to it.
6. Static/boilerplate text (headings, standard legal or formal
   language, labels) is written as literal strings exactly as
   always.
7. If a value the document needs is genuinely absent from case_data,
   do not fabricate it and do not insert a bracket placeholder —
   omit that specific detail as gracefully as the surrounding
   sentence allows rather than inventing or templating it.
8. Because every value is fully resolved and hardcoded, there are no
   defaults, no fallbacks, and no runtime inputs to manage anywhere
   in the generated code.
9. Future edits to any value happen by directly editing the literal
   text inside the specific function that contains it — never by
   reintroducing a parameter to that function.

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
9. Ensure functions are self-contained and independently callable.
10. Ensure generated code can be assembled later.

==================================================================
ASSEMBLY RULES
==================================================================

Generate:

export function buildDocument()

This function must:

1. Create document sections.
2. Call all generated functions, each with no arguments.
3. Preserve execution order.
4. Preserve section ordering.
5. Preserve header/footer ordering.
6. Return a complete DOCX.js document.
7. Return:

   new Document({{...}})

8. The returned Document must be directly executable without modification.
9. The returned Document must support DOCX export.
10. The returned Document must support real-time preview rendering.
11. buildDocument itself takes no parameters — every value it needs
    is already fully resolved inside the functions it calls.
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
9. Contain zero functions (including buildDocument) that declare or
   accept any parameters.
10. Contain zero references to caseData or any other external/data
    variable — every value must already be a resolved literal.

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