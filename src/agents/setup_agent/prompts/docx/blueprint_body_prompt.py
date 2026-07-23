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

The Formatting Blueprint should explicitly describe:
- paragraph alignment (e.g. Left, Center, Right, Justified)
- intentional blank spacer paragraphs
- tab stops and shared tab stop positions
- underlines (text-based vs drawn rule)
- page/section breaks
- numerical values whenever available (alignment, indents, tab stops, spacing, font size, bold/italic runs)
- any layout that cannot be inferred from the text alone

Preserve reconstruction-critical formatting without polluting the document text.

- For every run, state font_name and color explicitly if present in JSON — never omit.
- For table cell borders with a color value, state it explicitly — never drop it.

For ordinary body paragraphs sharing the same default layout and typography, describe the formatting ONCE for the entire group rather than repeating identical descriptions.

Only generate detailed formatting when it differs within the section or is visually significant.

Do NOT guess values.

--------------------------------------------------------------------

## Tables

Whenever tables exist:
Render them as Markdown tables.
Preserve row order, column order, merged cells, alignment, formatting, headers, and cell contents.
Table column count must exactly match the number of columns in table_data — never merge or drop a column because its cells are empty for most/all rows. Render empty cells as blank markdown cells, not as an omitted column. A column with only one non-empty value (e.g. one row showing "14A." while the rest are blank) is still a real column and must appear in every row of that table's output.

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
