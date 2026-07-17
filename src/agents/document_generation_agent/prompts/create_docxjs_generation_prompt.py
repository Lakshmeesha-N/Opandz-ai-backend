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
10. Ensure all elements fit completely within the section page dimensions and margins; no element (especially tables) should ever overflow or go out of the document boundaries.

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
BLUEPRINT RELIABILITY & CORRECTION RULES
==================================================================

1. Trust blueprint CONTENT (text, values, order) always. Trust its
   FORMATTING numbers (widths, spacing, margins, font size) only if
   they don't break the page.
2. Fix a formatting value ONLY if it does one of these:
   - table column widths add up to more than the page width
   - a margin/width/height is zero, negative, or bigger than the page
   - font size or spacing on one block wildly clashes with its
     siblings (classic PDF-extraction glitch)
   - anything would visually overlap or run off the page
3. If none of the above apply, leave the blueprint value as-is.
4. Fix with the smallest change that restores a valid layout — never
   delete content, never comment on the fix in the output.

==================================================================
OVERFLOW & SIZE ADJUSTMENT RULES
==================================================================

1. When injecting case data, the text length may vary and could be significantly longer than the original template text.
2. If you expect that the injected case data values will cause a table cell, column, or paragraph to overflow or look cluttered, you must intelligently adjust layout sizes:
   - Slightly reduce font sizes (e.g. from 12pt to 10pt or 11pt) to fit the text.
   - Adjust table column widths to allocate more space for longer content.
   - Decrease paragraph spacing (`before`, `after`) or line spacing to keep content within page boundaries.
3. All elements (including tables, cells, paragraphs, and lists) must strictly fit inside the document margins and page dimensions. They must not overflow or extend outside the printable area of the document.
4. Ensure the total width of all columns in any table does not exceed the printable page width (Page Width - Left Margin - Right Margin).

==================================================================
DOCX.JS API RULES  (READ EVERY RULE — VIOLATIONS CAUSE RUNTIME ERRORS)
==================================================================

IMPORTS
-------
1. Always import from "docx" at the top of the file.
2. Every class you use MUST be in the import list. Never use an
   undeclared identifier.
3. The required base imports are:
     import {{
       Document, Packer, Paragraph, TextRun, Header, Footer,
       Table, TableRow, TableCell, WidthType, AlignmentType,
       HeadingLevel, BorderStyle, ShadingType, PageOrientation,
       convertInchesToTwip, LevelFormat, UnderlineType,
       SectionType, PageNumber, NumberFormat, ImageRun,
       TableOfContents, ExternalHyperlink, InternalHyperlink,
       Bookmark, Tab, Leader, TabStopType, TabStopLeader
     }} from "docx";
4. Only include imports that are actually used in the file.

HEADER & FOOTER RULES  ← MOST COMMON SOURCE OF ERRORS
------------------------------------------------------
5. Header functions MUST return a `new Header({{ children: [...] }})`.
   NEVER return a bare `Paragraph` or array from a header function.
   CORRECT:
     export function build_section_header() {{
       return new Header({{ children: [new Paragraph({{ ... }})] }});
     }}
   WRONG (causes "Cannot read properties of undefined"):
     export function build_section_header() {{
       return new Paragraph({{ ... }});   // ← FORBIDDEN
     }}

6. Footer functions MUST return a `new Footer({{ children: [...] }})`.
   NEVER return a bare `Paragraph` or array from a footer function.
   CORRECT:
     export function build_section_footer() {{
       return new Footer({{ children: [new Paragraph({{ ... }})] }});
     }}
   WRONG:
     export function build_section_footer() {{
       return new Paragraph({{ ... }});   // ← FORBIDDEN
     }}

7. When assigning headers/footers in a Document section, always use
   the result of the header/footer function directly:
     headers: {{ default: build_section_header() }}
     footers: {{ default: build_section_footer() }}
   Never pass a Paragraph, array, or any other type there.

PARAGRAPH RULES
---------------
8. Every Paragraph must use the object-form constructor:
     new Paragraph({{ children: [...], ...options }})
   NEVER use the deprecated string-form:
     new Paragraph("text")   // ← FORBIDDEN — causes runtime errors

9. Text content goes inside `TextRun` objects within `children`:
     new Paragraph({{
       children: [new TextRun({{ text: "Hello", bold: true }})]
     }})

10. `Paragraph` accepts these top-level options (not inside children):
    - alignment, heading, spacing, indent, style, border, shading,
      pageBreakBefore, keepNext, keepLines, outlineLevel, numbering,
      tabStops, thematicBreak, contextualSpacing.

TEXTRUN RULES
-------------
11. TextRun properties: text, bold, italics, underline, strike,
    color, size, font, highlight, allCaps, smallCaps, break,
    characterSpacing, vanish, specVanish, emphasisMark, language,
    superScript, subScript.
12. `size` is in half-points (e.g., 24 = 12pt, 28 = 14pt).
13. `color` is a 6-digit hex string WITHOUT the "#" prefix:
    CORRECT: color: "FF0000"   WRONG: color: "#FF0000"

TABLE RULES
-----------
14. Table structure:
      new Table({{
        rows: [
          new TableRow({{
            children: [
              new TableCell({{ children: [new Paragraph({{ children: [] }})] }}),
            ]
          }})
        ]
      }})
15. Every TableCell MUST have at least one Paragraph in its children.
    An empty TableCell MUST still contain: children: [new Paragraph({{}})]
16. Width of columns uses WidthType:
      width: {{ size: 50, type: WidthType.PERCENTAGE }}
      width: {{ size: convertInchesToTwip(2), type: WidthType.DXA }}

DOCUMENT / SECTION RULES
--------------------------
17. Document sections are defined as an array under the `sections` key:
      new Document({{
        sections: [
          {{
            properties: {{ ... }},
            headers: {{ default: build_section_1_header() }},
            footers: {{ default: build_section_1_footer() }},
            children: [ ...build_01_group(), ...build_02_group() ]
          }}
        ]
      }})
18. `children` in a section is a flat array of Paragraph and Table
    objects — never nested arrays. Spread group function results if they
    return arrays: `...build_02_group()`.
19. Section `properties` for page size/margins:
      The blueprint/config specifies the page width, height, and margins directly in Twips. Write these values directly in the generated JavaScript code as numbers. Do NOT wrap them in `convertInchesToTwip()` since they are already in Twips.
      Example:
        properties: {{
          page: {{
            margin: {{
              top: 1440,
              bottom: 1440,
              left: 1800,
              right: 1800,
            }},
            size: {{
              width: 12240,
              height: 15840,
            }}
          }}
        }}

SPACING RULES
-------------
20. Paragraph spacing and indents use twips. The blueprint/config specifies spacing (before, after) and indents (left, right, etc.) directly in Twips. Write these values directly as numbers. Do NOT multiply them by 20 or wrap them in convertInchesToTwip since they are already in Twips.
      Example:
        spacing: {{ before: 240, after: 120, line: 240, lineRule: "auto" }}

GENERAL RULES
-------------
21. Use DOCX.js constructs only — no DOM, no Node.js fs, no Buffer.
22. Generate valid JavaScript — all brackets, braces, and parentheses
    must be balanced.
23. Generate production-ready code with no TODO comments or stubs.
24. Export every generated function with the `export` keyword.
25. Avoid duplicate code — extract shared styles/options to const
    variables at the top of the file.
26. Avoid circular dependencies between functions.
27. Ensure functions are self-contained and independently callable.

==================================================================
ASSEMBLY RULES
==================================================================

Generate:

export function buildDocument()

This function must:

1. Create document sections.
2. Call all generated functions, each with no arguments.
3. Preserve execution order — sections and groups in blueprint order.
4. Preserve section ordering.
5. Preserve header/footer ordering.
6. Return a complete DOCX.js document.
7. Return:

   new Document({{ sections: [ ... ] }})

8. headers and footers in each section object MUST use the wrapper
   objects returned by build_..._header() and build_..._footer().
   Example:
     {{
       headers: {{ default: build_section_1_header() }},
       footers: {{ default: build_section_1_footer() }},
       children: [ ...build_01_group(), ...build_02_group() ]
     }}
9. The returned Document must be directly executable without
   modification — it must produce a valid .docx file when passed to
   Packer.toBuffer().
10. The returned Document must support DOCX export.
11. The returned Document must support real-time preview rendering.
12. buildDocument itself takes no parameters — every value it needs
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