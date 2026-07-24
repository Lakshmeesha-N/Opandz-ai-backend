# src/agents/document_generation_agent/prompts/create_section_docxjs_prompt.py


def create_section_docxjs_prompt(
    fn_name: str,
    section_markdown: str,
    case_data: dict,
    metadata_md: str,
    is_header: bool = False,
    is_footer: bool = False,
) -> str:
    """
    Build a focused prompt to generate exactly ONE DOCX.js export function
    for a single blueprint section.
    """

    if is_header:
        return_type_hint = "new Header({ children: [...] })"
        extra_rule = (
            "This function MUST return `new Header({ children: [...] })`.\n"
            "NEVER return a bare Paragraph or an array from a header function."
        )
    elif is_footer:
        return_type_hint = "new Footer({ children: [...] })"
        extra_rule = (
            "This function MUST return `new Footer({ children: [...] })`.\n"
            "NEVER return a bare Paragraph or an array from a footer function."
        )
    else:
        return_type_hint = "an Array of Paragraph/Table objects"
        extra_rule = (
            "This function MUST return an Array of Paragraph and/or Table objects.\n"
            "Example: return [ new Paragraph({...}), new Table({...}), ... ]"
        )

    return f"""You are a DOCX.js code generator. Your task is to generate EXACTLY ONE export function.

==================================================================
FUNCTION TO GENERATE
==================================================================

Function name : {fn_name}
Return value  : {return_type_hint}

{extra_rule}

==================================================================
RULES & PROFESSIONAL QUALITY MANDATE
==================================================================

CRITICAL ROLE DIRECTIVE (60% BLUEPRINT REFERENCE / 40% EXPERT KNOWLEDGE):
- The Blueprint below provides approximately 60% structural reference.
- The remaining 40% MUST come from your expertise as a MASTER DOCUMENT WRITER and DOCX.JS ARCHITECT.
- The output document MUST look 100% professional, elegant, and unbroken. It should NOT look broken or visually distorted.
- If any formatting, column width, line height, table padding, or alignment in the blueprint is missing, broken, or ambiguous, it is YOUR DIRECT RESPONSIBILITY to apply expert document design standards to fix and refine it.

1. Output ONLY the single export function — no imports, no other functions.
2. Every piece of text in ORIGINAL CONTENT below must appear verbatim.
   Do NOT paraphrase, shorten, summarize, or skip any line.
3. Every table row listed in ORIGINAL CONTENT must become a TableRow in code.
   Never skip a row. Never merge rows.
4. Every numbered or bulleted item must become its own Paragraph.
5. DOCX.JS API NAMES (MANDATORY — use EXACTLY these):
   - Alignment MUST be `AlignmentType.CENTER`, `AlignmentType.LEFT`, `AlignmentType.RIGHT`, `AlignmentType.BOTH`.
     NEVER use `Alignment.CENTER` or `Alignment.LEFT` — those do NOT exist.
   - Line rule MUST be `LineRuleType.MULTIPLE`, `LineRuleType.EXACT`, `LineRuleType.AT_LEAST`.
     NEVER use `LineRule.MULTIPLE` — `LineRule` does NOT exist in `docx`.
   - Height rule MUST be `HeightRuleType.EXACT`, `HeightRuleType.AT_LEAST`.
     NEVER use `HeightRule.EXACT` — `HeightRule` does NOT exist in `docx`.
   - Table cell width: `WidthType.DXA` (not `WidthType.TWIPS`)
   - Border style: `BorderStyle.SINGLE`, `BorderStyle.NONE` etc.
   - Underline: `UnderlineType.SINGLE`
   - NEVER define a const CASE_DATA object inside the function. Use case data values directly as string literals.

5. PER-RUN FORMATTING (CRITICAL — read the Formatting Blueprint Run entries):
   - The blueprint lists every text run as: "text" | bold=X | italic=X | underline=X | font=X | size=Xpt | color=#RRGGBB
   - You MUST implement EACH run as a separate `new TextRun({{...}})` inside the Paragraph children array.
   - bold=true → `bold: true` in TextRun. bold=false → omit bold. NEVER apply bold to a whole Paragraph.
   - underline=true → `underline: {{ type: UnderlineType.SINGLE }}` in TextRun. NEVER apply underline to a whole Paragraph.
   - italic=true → `italic: true` in TextRun.
   - font=<name> → `font: "<name>"` in TextRun.
   - size=Xpt → `size: X*2` in TextRun (DOCX.js uses half-points; multiply pt value by 2).
   - color=#RRGGBB → `color: "RRGGBB"` in TextRun (NO # prefix).
   - If blueprint says "All runs:" one entry applies to all runs in that paragraph.

6. PER-TABLE FORMATTING (CRITICAL — read the Table Formatting Spec):
   - Blueprint states: Column widths (in POINTS): Col1=Xpt | Col2=Xpt | ...
     → Convert to twips: `width: {{ size: X*20, type: WidthType.DXA }}` per column (1pt = 20 twips).
   - Blueprint states: Cell 1: width=Xpt
     → Apply `width: {{ size: X*20, type: WidthType.DXA }}` to each TableCell.
   - Blueprint states: vAlign=top/center/bottom
     → Apply `verticalAlign: "top" | "center" | "bottom"` to each TableCell.
   - Blueprint states: Row height: Xpt (exact | atLeast | auto)
     → Apply `height: X*20, cantSplit: false` to TableRow when exact or atLeast.
   - Blueprint states: Cell borders differ from table default
     → Apply per-cell border overrides with exact style, size, and color.
   - Blueprint states: colspan=N
     → Apply `columnSpan: N` to TableCell.
   - Blueprint states: Table borders top/bottom/left/right/insideH/insideV
     → Apply to `borders` in Table constructor using BorderStyle values.

   LAYOUT TABLE AUTO-CORRECTION (CRITICAL):
   - If a table has NO visible borders (borderless layout table) AND all column widths are equal AND narrow (each column < 200pt) AND the section contains a cause title pattern (Claimant/Respondent labels + addresses), this is a PDF-conversion artifact — the column widths are WRONG.
   - For cause title / party layout tables (Claimant, Respondent, V/s sections), ALWAYS use these column widths regardless of what the blueprint states:
     * 3-column layout: Col1 = 1260 twips (label), Col2 = 540 twips (colon), Col3 = 6480 twips (name/address)
     * 4-column layout: Col1 = 1260 twips (label), Col2 = 540 twips (colon), Col3 = 540 twips (number), Col4 = 5940 twips (name/address)
   - Set `verticalAlign: "top"` on ALL cells in layout tables.
   - NEVER put all address lines in a single TextRun. Each address line (Name, S/o, Aged, R/at, city) MUST be a SEPARATE `new Paragraph({{ children: [new TextRun({{...}})] }})` inside the cell's children array.

7. All spacing/indent values in the FORMATTING BLUEPRINT are in POINTS unless explicitly stated as twips.
   - Convert points to twips: multiply by 20 (e.g. `space_before: 6pt` → `before: 120`).
   - Tab stops in points: multiply by 20 for twips.

8. STRICT PAGE FLOW RULE (NO ARTIFICIAL PAGE BREAKS):
   - NEVER set `pageBreakBefore: true` on any Paragraph.
   - NEVER add `break: true` or `new PageBreak()` on any TextRun unless the blueprint explicitly contains a `[PAGE BREAK]` marker.
   - All section functions MUST return elements that flow continuously on the page. Let Word/DOCX engine perform natural pagination.

9. Every TableCell MUST contain at least one Paragraph, even if empty.
10. Never use new Paragraph("string") — always use new Paragraph({{ children: [new TextRun({{...}})] }}).
11. All text content comes from ORIGINAL CONTENT and CASE DATA combined.
    Replace any placeholder-like values (e.g. blank M.V.C. number, empty date)
    with values from CASE DATA when a matching field exists.
12. The function signature is:  export function {fn_name}()  — zero parameters.
12. Generate production-ready code — no TODO comments, no stubs, no ellipses.

==================================================================
PAGE SETUP CONTEXT (for reference — do NOT output page/section objects)
==================================================================

{metadata_md}

==================================================================
CASE DATA
==================================================================

{case_data}

==================================================================
SECTION TO IMPLEMENT
==================================================================

{section_markdown}

==================================================================
OUTPUT
==================================================================

Output ONLY the complete export function. Start with:
export function {fn_name}() {{
"""
