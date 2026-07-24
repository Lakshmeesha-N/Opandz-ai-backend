# src/agents/document_generation_agent/helpers/create_docxjs_generation_prompt.py

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)


def create_docxjs_generation_prompt(
    state: AgentState,
) -> str:

    return f"""
You are an expert DOCX.js engineer and document rendering architect.

Your task is to generate production-ready DOCX.js code from the provided blueprint and case data.

==================================================================
INPUTS PROVIDED
==================================================================

1. case_data
2. blueprint  (a Markdown reconstruction spec — NOT raw JSON. It is
   organized into named semantic sections, each with prose layout
   logic, a verbatim text/code-block mockup, and a bullet list of
   exact formatting values. It does NOT contain block_id references.)

==================================================================
READING THE BLUEPRINT FORMAT
==================================================================

1. The blueprint is divided into "## Section Name" headings. Each
   heading names a semantic unit (e.g. "Claimants List Block",
   "Particulars Table 1", "Running Header", "Page Footer").
2. A section named "Running Header" or similar describes content that
   repeats at the top of every page/section — this maps to a DOCX.js
   Header. A section named "Page Footer" or similar maps to a Footer.
   Treat ONLY these explicitly-named repeating sections as
   Header/Footer objects — every other section is body content.
3. Any other section is BODY content — even if it mentions a report
   title, chapter label, or similar; only build it as a Header/Footer
   if the blueprint explicitly names it as a repeating header/footer
   section.
4. If a section's bullets reference "(repeating [element], same as
   Section N)", resolve this by reusing the exact content and
   formatting already defined in Section N when generating this
   section's function — do not skip it, do not leave it blank. Every
   section function must be fully self-contained and independently
   correct, even though the blueprint deduplicated the description.
5. Table sections render as literal Markdown tables in the blueprint
   — every row and column must be reproduced, including blank cells,
   exactly matching the blueprint's column count. Never merge or drop
   a column because its cells are mostly empty.
6. Code-block mockups (spatially arranged verbatim text) are the
   authoritative source for exact text content and reading order —
   reproduce every word from inside them, never paraphrase or drop
   any line, including blank/spacer lines.
7. Bullet lists under each section give exact numeric formatting
   values (indent, spacing, alignment, tab-stops, line spacing, font,
   color, bold/italic runs) — use these values directly, never
   recompute or approximate them, except where OVERFLOW & SIZE
   ADJUSTMENT RULES or BLUEPRINT RELIABILITY rules below apply.
8. If a bullet states "not specified in source data" for a value, use
   a sane DOCX.js default for that property rather than inventing a
   specific number.

==================================================================
GOAL
==================================================================

Generate a complete DOCX.js implementation that can recreate the entire document.

==================================================================
GENERIC MANDATE: 100% COMPLETE VERBATIM RECREATION FOR ALL DOCUMENTS
==================================================================

1. FULL CONTENT PRESERVATION: You MUST generate 100% of all content, text, tables, and sections present in the provided BLUEPRINT into DOCX.js code.
2. ZERO OMISSION OF TABLE ROWS: In EVERY table present in the blueprint, EVERY single row (from the first row to the last row, including all intermediate numbered rows, data rows, and blank cells) MUST be explicitly created as a TableRow object in DOCX.js. Never skip, skip-count, or summarize table rows.
3. ZERO OMISSION OF PARAGRAPHS & LISTS: Every single paragraph, narrative section, numbered/bullet list item, prayer section, legal clause, signature block, advocate line, and verification block in the blueprint MUST be rendered in complete verbatim detail.
4. NO TRUNCATION / NO STUBS / NO ELLIPSES: Never output ellipses ("..."), TODO comments, summary stubs, or shortened text (such as "Wherefore, it is respectfully prayed..." or "That on an ill-fated day..."). Every paragraph, table cell, legal clause, signature block, and string from the blueprint and case_data MUST be written out in full verbatim text.
5. NO DOCUMENT BIAS: These rules apply universally to EVERY template and document blueprint processed by this agent.

The generated code must contain:

1. One function for every section explicitly identified as a
   repeating header (e.g. "Running Header").
2. One function for every other semantic section in the blueprint
   (in the order they appear).
3. One function for every section explicitly identified as a
   repeating footer (e.g. "Page Footer").
4. One final buildDocument() function that assembles the document.

Every one of these functions is fully self-contained and takes zero
parameters. See FUNCTION SIGNATURE RULES below.

==================================================================
FUNCTION NAMING RULES
==================================================================

CRITICAL: Derive function names directly from the blueprint's actual
"## Section Name" headings — do not invent generic names and do not
copy any example names shown in these instructions.

Header section (explicitly named repeating header):
"Running Header" → build_section_header()

Ordinary semantic section, in blueprint order, numbered sequentially:
"Claimants List Block" (1st body section) → build_01_claimants_list_block()
"Particulars Table 1" (2nd body section) → build_02_particulars_table_1()

Footer section (explicitly named repeating footer):
"Page Footer" → build_section_footer()

Use snake_case derived from the actual heading text, prefixed with a
zero-padded sequence number for ordinary body sections only (not for
the header/footer functions).

==================================================================
FUNCTION SIGNATURE RULES
==================================================================

1. Every function — every header function, every footer function,
   every semantic-section function, and buildDocument — is defined
   with ZERO parameters. No exceptions.
2. No function signature may include caseData, data, params, or any
   other parameter name, under any circumstance.
3. All content a function needs is written directly inside that
   function as fully resolved literal text, taken from the blueprint
   and case_data. Nothing is passed in from outside and nothing is
   read from an external variable.
4. buildDocument() itself takes no parameters and calls every other
   function with no arguments.
5. If a function currently under construction would only make sense
   with a parameter, that is a signal the value it needs must
   instead be resolved now and hardcoded directly into that
   function's literal text — not solved by adding a parameter.

==================================================================
SECTION HANDLING RULES
==================================================================

1. The blueprint may describe multiple document sections (distinct
   page-setup groups, e.g. different margins/orientation) as well as
   multiple semantic content sections within each. Handle all of them.
2. Respect section boundaries exactly as delineated by blueprint
   headings.
3. Respect execution order — blueprint order is document order.
4. Respect section metadata (page dimensions, margins, orientation)
   as given in the blueprint's Page Setup / Recurring Layout
   Constants information.
5. Respect section-specific formatting differences (e.g. a section
   with a different top margin).
6. Respect content ordering within each section.
7. Ensure all elements fit completely within the page dimensions and
   margins; no element (especially tables) should ever overflow or
   extend past document boundaries.

==================================================================
BLUEPRINT RULES (STRICT 100% COMPLETENESS REQUIRED)
==================================================================

CRITICAL COMPLETENESS MANDATE:
1. You MUST generate 100% of all content present in the BLUEPRINT into DOCX.js code.
2. NEVER skip, truncate, summarize, abbreviate, or omit any table rows, paragraphs, bullet points, narrative sections, prayer requests, heads of claim, signature blocks, or verification blocks.
3. IN TABLES: Every single row listed in the blueprint (e.g. Items 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14(a), 15, 16, 17, 18, 19, 20, 21, 22) MUST be explicitly created as a TableRow in DOCX.js with complete text and formatting. Omitting intermediate rows or skipping numbers is FORBIDDEN.
4. IN NARRATIVES & PRAYERS: Every paragraph (including long incident descriptions), all listed heads of compensation (Items 1 through 8), charge sheet descriptions, prayer demands, advocate signature blocks, claimant signature blocks, and verification text MUST be rendered in full verbatim detail.
5. Preserve repeating header content.
6. Preserve all body content verbatim.
7. Preserve repeating footer content.
8. Preserve headings.
9. Preserve paragraphs, including empty spacer paragraphs where the blueprint notes them.
10. Preserve spacing values exactly as given.
11. Preserve alignment exactly as given.
12. Preserve indentation exactly as given.
13. Preserve named styles referenced in the blueprint.
14. Preserve run-level formatting (bold/italic/underline substrings).
15. Preserve font colors exactly as given (hex values from the blueprint).
16. Preserve font sizes and font names exactly as given.
17. Preserve table structures (column widths, border color/weight).

==================================================================
BLUEPRINT RELIABILITY & CONTENT INTEGRITY
==================================================================

1. CONTENT IS MANDATORY: All text content, table rows, and structural elements from the blueprint must be preserved 100% without exception. You are NOT allowed to omit or summarize any text.
2. VISUAL LAYOUT ADJUSTMENT: Your professional judgment applies ONLY to fixing visual layout calculations (e.g., column width math, line spacing rule conversions, font size overflow adjustments).
3. NEVER delete real text or skip table rows to fix a formatting issue.
4. If verbatim text contains embedded literal "\\n" sequences, split on "\\n" and render each line as its own Paragraph so text flows cleanly. NEVER drop lines.

When generating DOCX.js code, produce the complete, 100% comprehensive, court-ready document with zero missing sections or omitted rows.

==================================================================
OVERFLOW & SIZE ADJUSTMENT RULES
==================================================================

1. When injecting case data, text length may vary and could be
   significantly longer than the original template text.
2. If injected case data values will cause a table cell, column, or
   paragraph to overflow or look cluttered, intelligently adjust:
   - Slightly reduce font sizes to fit the text.
   - Adjust table column widths to allocate more space for longer
     content.
   - Decrease paragraph/line spacing to keep content within bounds.
3. All elements must strictly fit inside the document margins and
   page dimensions given in the blueprint's Page Setup section.
4. Ensure the total width of all table columns never exceeds the
   printable page width (Page Width - Left Margin - Right Margin).

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
6. Footer functions MUST return a `new Footer({{ children: [...] }})`.
   NEVER return a bare `Paragraph` or array from a footer function.
7. When assigning headers/footers in a Document section, always use
   the result of the header/footer function directly:
     headers: {{ default: build_section_header() }}
     footers: {{ default: build_section_footer() }}
   Never pass a Paragraph, array, or any other type there.

PARAGRAPH RULES
---------------
8. Every Paragraph must use the object-form constructor:
     new Paragraph({{ children: [...], ...options }})
   NEVER use the deprecated string-form: new Paragraph("text").
9. Text content goes inside `TextRun` objects within `children`.
10. `Paragraph` accepts these top-level options (not inside children):
    alignment, heading, spacing, indent, style, border, shading,
    pageBreakBefore, keepNext, keepLines, outlineLevel, numbering,
    tabStops, thematicBreak, contextualSpacing.

TEXTRUN RULES
-------------
11. TextRun properties: text, bold, italics, underline, strike,
    color, size, font, highlight, allCaps, smallCaps, break,
    characterSpacing, vanish, specVanish, emphasisMark, language,
    superScript, subScript.
12. `size` is in half-points (e.g., 24 = 12pt, 28 = 14pt). If the
    blueprint gives a size directly in points, multiply by 2 before
    writing it as `size`.
13. `color` is a 6-digit hex string WITHOUT the "#" prefix. If the
    blueprint gives a color with a leading "#", strip it.

TABLE RULES
-----------
14. Table structure uses TableRow/TableCell with Paragraph children.
15. Every TableCell MUST have at least one Paragraph, even if empty:
    children: [new Paragraph({{}})].
16. Width of columns uses WidthType:
      width: {{ size: 50, type: WidthType.PERCENTAGE }}
      width: {{ size: convertInchesToTwip(2), type: WidthType.DXA }}

DOCUMENT / SECTION RULES
--------------------------
17. Document sections are defined as an array under the `sections`
    key, each with properties/headers/footers/children.
18. `children` in a section is a flat array of Paragraph and Table
    objects — never nested arrays. Spread group function results:
    `...build_01_claimants_list_block()`.
19. Section `properties` for page size/margins: the blueprint
    specifies page width, height, and margins directly in Twips.
    Write these values directly as numbers — do NOT wrap them in
    convertInchesToTwip() since they are already in Twips.

SPACING RULES
-------------
20. Paragraph spacing and indents from the blueprint are already in
    Twips (or in points — check the stated unit). Write Twips values
    directly as numbers. If a value is stated in points, convert to
    twips by multiplying by 20 before writing it.
21. Line spacing in the blueprint may be stated as a multiplier
    (e.g. "1.8×") or as an exact twips value (e.g. "276 twips
    exactly"). Convert as follows — never write the raw stated number
    directly into docx.js without this conversion:
      - multiplier: line = round(value * 240), lineRule: "auto"
      - exact twips: line = value, lineRule: "exact"
    Getting this conversion wrong causes paragraphs to collapse and
    visually overlap with the line below — treat this rule as strict.

GENERAL RULES
-------------
22. Use DOCX.js constructs only — no DOM, no Node.js fs, no Buffer.
23. Generate valid JavaScript — all brackets, braces, and parentheses
    must be balanced.
24. Generate production-ready code with no TODO comments or stubs.
25. Export every generated function with the `export` keyword.
26. Avoid duplicate code — extract shared styles/options to const
    variables at the top of the file.
27. Avoid circular dependencies between functions.
28. Ensure functions are self-contained and independently callable.

==================================================================
ASSEMBLY RULES
==================================================================

Generate:

export function buildDocument()

This function must:

1. Create document sections matching the blueprint's Page Setup
   groupings.
2. Call all generated functions, each with no arguments.
3. Preserve execution order — sections and groups in blueprint order.
4. Preserve section ordering.
5. Preserve header/footer ordering.
6. Return a complete DOCX.js document:
     new Document({{ sections: [ ... ] }})
7. headers and footers in each section object MUST use the wrapper
   objects returned by build_section_header() and
   build_section_footer().
8. The returned Document must be directly executable without
   modification — it must produce a valid .docx file when passed to
   Packer.toBuffer().
9. The returned Document must support real-time preview rendering.
10. buildDocument itself takes no parameters — every value it needs
    is already fully resolved inside the functions it calls.

==================================================================
VALIDATION RULES
==================================================================

The generated code MUST:

1. Compile successfully.
2. Execute without syntax or runtime errors.
3. Be importable and exportable.
4. Be production ready.
5. Support future insertion of additional semantic sections.
6. Contain zero functions (including buildDocument) that declare or
   accept any parameters.
7. Contain zero references to caseData or any other external/data
   variable — every value must already be a resolved literal.
8. Reproduce every section named in the blueprint — no section may be
   silently skipped, including repeating header/footer resolution
   for every occurrence noted as "(same as Section N)".

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

{state.get("case_data", {})}

==================================================================
BLUEPRINT
==================================================================

{state.get("blueprint", "")}
"""