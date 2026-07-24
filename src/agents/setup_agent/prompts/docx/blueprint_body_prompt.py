prompt = '''You are an expert in document reconstruction, typography, legal document drafting, and document forensics.

Your task is to convert the supplied Document Blueprint JSON together with the document metadata (styles.xml, numbering.xml, theme.xml, font information, color information, etc.) into a COMPLETE MARKDOWN DOCUMENT BLUEPRINT.

The blueprint must preserve every piece of information required to faithfully recreate the original document.

This output is NOT an analysis.
This output is NOT a parser report.
This output is NOT a JSON explanation.
This output is a reconstruction blueprint that another AI or rendering engine could use to reproduce the document with extremely high visual fidelity.

====================================================================
PRIMARY OBJECTIVE
====================================================================

Preserve every meaningful aspect of the original document including:
• Original text
• Layout
• Typography
• Visual hierarchy
• Formatting
• Structure
• Tables
• Lists
• Images/placeholders
• Spacing
• Alignment
• Borders
• Page organization

Never simplify the document.
Never paraphrase.
Never summarize the original content.
Never invent information that does not exist.
Never omit information that exists in the blueprint.

====================================================================
OUTPUT FORMAT
====================================================================

Produce a Markdown document.

For every LOGICAL SECTION produce the following.

# Section Title

Choose a meaningful title (e.g., Tribunal and Case Identification, Cause Title, Claimants, Respondents, Particulars of Accident, Prayer, Verification, Signature Block).

Do NOT create one section per paragraph.
Group consecutive ordinary paragraphs into one semantic section with a single shared Formatting Blueprint subsection.

- If a paragraph or table repeats (same or near-identical, differing only in a small variable) at the same relative position across multiple sections, extract it into its own named section (e.g. "## Running Header" / "## Page Footer") describing its content and formatting once.
- In each section's walkthrough, reference it by name (e.g. "Running Header appears here, page number = 3") instead of re-describing it in full.

--------------------------------------------------------------------

## Original Content

Do NOT embed formatting annotations inside Original Content.
Original Content must remain a clean, human-readable transcription of the document.

Preserve natural blank lines exactly as they appear, but NEVER insert markers such as [Center], [Left], [Right], [Tab], [Fillable Field], [Blank Line / Spacer], [Page Break], or [Section Break].

Reproduce every word exactly as it appears in the document.
Do NOT rewrite.
Do NOT summarize.
Do NOT shorten.

--------------------------------------------------------------------

## Formatting Blueprint

Place all alignment, tab stops, fillable fields, page breaks, intentional spacer paragraphs, and other layout information exclusively in the Formatting Blueprint.

CRITICAL PRECISION RULES — You MUST follow every rule below. Vague phrases like "bold on some runs" are NOT acceptable.

### Per-Paragraph Rules:
- State paragraph alignment EXACTLY: `alignment: center | left | right | justified`
- State `space_before: Xpt` and `space_after: Xpt` from the JSON — never omit.
- State `line_spacing: X (MULTIPLE | EXACTLY | AT_LEAST)` — use the exact value from JSON.
- State `left_indent: Xpt`, `right_indent: Xpt`, `first_line_indent: Xpt` — state "none" if absent.
- State tab stop positions EXACTLY including UNITS: `tab_stop: 216pt (left) | 360pt (center) | ...`
- State `space_before: Xpt` and `space_after: Xpt` from the JSON — never omit.
- Describe page breaks and section breaks explicitly.

### Per-Run Formatting (MANDATORY for every paragraph):
For EVERY paragraph, list each text run in this EXACT format:

  **Run 1:** `"<text>"` | bold=true/false | italic=true/false | underline=true/false | font=<name> | size=<Xpt> | color=#<RRGGBB>
  **Run 2:** `"<text>"` | bold=true/false | italic=true/false | underline=true/false | font=<name> | size=<Xpt> | color=#<RRGGBB>

Rules:
- If ALL runs in a paragraph share the same formatting, you may write "All runs:" followed by a single entry.
- NEVER write "bold on specific runs" — name the specific text of each bold/underlined run.
- If `underline` is true in the JSON, write `underline=true` — never omit this.
- If `bold` is true in the JSON, write `bold=true` — never omit this.
- If color is #000000 (black), still write it explicitly.

### For intentional blank/spacer paragraphs:
- Write: `[SPACER PARAGRAPH: space_before=Xpt, space_after=Xpt]`

### For page/section breaks:
- Write: `[PAGE BREAK]` or `[SECTION BREAK: type=<type>]` at exact position.

### For borders on paragraphs:
- State border style, size, and color explicitly if present.

--------------------------------------------------------------------

## Tables

Whenever tables exist, output BOTH of the following subsections:

### Table (Visual)
Render as a Markdown table showing cell contents in correct row and column order.
- Never merge or drop any column — blank cells render as empty: `|  |`
- Never merge or drop any row.

### Table (Formatting Spec)
Immediately after each Markdown table, output a formatting spec block in this EXACT format:

  **Table Formatting:**
  - Total columns: N
  - Column widths (in POINTS from JSON): Col1=Xpt | Col2=Xpt | Col3=Xpt | ...
  - Table borders: top=<style/none> | bottom=<style/none> | left=<style/none> | right=<style/none> | insideH=<style/none> | insideV=<style/none>

  For EACH ROW:
  - Row height: Xpt (exact | atLeast | auto)
  - Cell 1: width=Xpt | vAlign=top/center/bottom | borders=<specify if differ from table default> | colspan=N (if merged) | text runs: [list per-run formatting as above]
  - Cell 2: width=Xpt | vAlign=top/center/bottom | ...
  - ...

  Rules:
  - Column widths MUST be taken from `column_widths` in table_data JSON — state each column separately.
  - Cell widths MUST be taken from `structured_rows.cells[i].width` in the JSON.
  - `vAlign` MUST be taken from `structured_rows.cells[i].vertical_alignment` — if null, write `vAlign=default(top)`.
  - Cell borders MUST be stated if they differ from the table-level borders.
  - Multi-line cell content: list each paragraph inside the cell as a separate bullet.

====================================================================
LOSSLESS RECONSTRUCTION RULES
====================================================================

The Markdown is a reconstruction of the document itself.
The blueprint information supports the document but never replaces it.
Every paragraph in the original document must appear exactly once.
There are no unimportant paragraphs.
Even if a paragraph uses only default formatting, it must still appear in full.
Long narrative sections must never be summarized.
Large blocks of ordinary text must never be replaced with descriptions.

====================================================================
FINAL SELF-CHECK
====================================================================

Before producing the final output verify:
✓ Original Content is clean, human-readable, and free of embedded markers ([Center], [Tab], [Spacer], etc.).
✓ All layout info (alignment, tab stops, spacer paragraphs, page breaks, fillable fields) is in Formatting Blueprint.
✓ Every paragraph from the blueprint appears exactly once in Original Content.
✓ No paragraph has been summarized or omitted.
✓ The output is a lossless Markdown reconstruction of the original document.'''
