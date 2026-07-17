# block_extractor.py

from typing import Any, List
from docx.text.paragraph import Paragraph
from docx.text.run import Run as DocxRun
from docx.table import Table, _Cell
from docx.oxml.ns import qn
from docx.enum.text import WD_LINE_SPACING

from src.agents.setup_agent.schema.docx_schema import (
    Run,
    ParagraphStyle,
    DocumentBlock,
)

EMU_PER_POINT = 12700


def _attr(element, name: str) -> str | None:
    if element is None:
        return None
    return element.get(qn(name))


def _child(element, name: str):
    if element is None:
        return None
    return element.find(qn(name))


def _children(element, name: str):
    if element is None:
        return []
    return element.findall(qn(name))


def _twips_to_points(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return int(value) / 20
    except (TypeError, ValueError):
        return None


def _emu_to_points(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return int(value) / EMU_PER_POINT
    except (TypeError, ValueError):
        return None


def _border_data(element) -> dict[str, Any] | None:
    if element is None:
        return None

    borders = {}
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        side_el = _child(element, f"w:{side}")
        if side_el is None:
            continue
        borders[side] = {
            "value": _attr(side_el, "w:val"),
            "size": int(_attr(side_el, "w:sz")) if (_attr(side_el, "w:sz") or "").isdigit() else None,
            "space": int(_attr(side_el, "w:space")) if (_attr(side_el, "w:space") or "").isdigit() else None,
            "color": _attr(side_el, "w:color"),
        }
    return borders or None


def _shading_data(element) -> dict[str, str | None] | None:
    shading = _child(element, "w:shd")
    if shading is None:
        return None
    return {
        "fill": _attr(shading, "w:fill"),
        "color": _attr(shading, "w:color"),
        "value": _attr(shading, "w:val"),
    }


def _numbering_data(paragraph: Paragraph) -> dict[str, str | None] | None:
    p_pr = _child(paragraph._p, "w:pPr")
    num_pr = _child(p_pr, "w:numPr")
    style_name = paragraph.style.name.lower() if paragraph.style and paragraph.style.name else ""

    list_type = None
    if "bullet" in style_name:
        list_type = "bullet"
    elif "number" in style_name or "list" in style_name:
        list_type = "numbered"

    if num_pr is None:
        if list_type is None:
            return None
        return {
            "num_id": None,
            "level": None,
            "list_type": list_type,
        }

    num_id_el = _child(num_pr, "w:numId")
    level_el = _child(num_pr, "w:ilvl")
    num_id = _attr(num_id_el, "w:val")
    level = _attr(level_el, "w:val")
    if list_type is None and num_id is not None:
        list_type = "numbered"

    return {
        "num_id": num_id,
        "level": level,
        "list_type": list_type,
    }


def _tab_stops(paragraph: Paragraph) -> list[dict[str, Any]] | None:
    p_pr = _child(paragraph._p, "w:pPr")
    tabs_el = _child(p_pr, "w:tabs")
    tabs = []
    for tab in _children(tabs_el, "w:tab"):
        tabs.append(
            {
                "position": _twips_to_points(_attr(tab, "w:pos")),
                "alignment": _attr(tab, "w:val"),
                "leader": _attr(tab, "w:leader"),
            }
        )
    return tabs or None


def _image_slots(paragraph: Paragraph) -> list[dict[str, Any]] | None:
    slots = []
    drawings = paragraph._p.xpath(".//w:drawing")
    picts = paragraph._p.xpath(".//w:pict")

    for drawing in drawings:
        blips = drawing.xpath(".//a:blip")
        extents = drawing.xpath(".//wp:extent")
        doc_props = drawing.xpath(".//wp:docPr")
        relationship_id = None
        if blips:
            relationship_id = blips[0].get(qn("r:embed")) or blips[0].get(qn("r:link"))
        extent = extents[0] if extents else None
        doc_prop = doc_props[0] if doc_props else None
        slots.append(
            {
                "has_image": True,
                "relationship_id": relationship_id,
                "name": doc_prop.get("name") if doc_prop is not None else None,
                "width": _emu_to_points(extent.get("cx")) if extent is not None else None,
                "height": _emu_to_points(extent.get("cy")) if extent is not None else None,
            }
        )

    for pict in picts:
        slots.append(
            {
                "has_image": True,
                "relationship_id": None,
                "name": None,
                "width": None,
                "height": None,
            }
        )

    return slots or None


def _hyperlink_url(paragraph: Paragraph, hyperlink_el) -> str | None:
    """
    Resolve a <w:hyperlink> element's r:id to its actual target URL
    via the paragraph's part relationships. Returns None for internal
    (anchor-only) hyperlinks with no r:id, or if the relationship is
    missing (which happens with some malformed/converted DOCX files).
    """
    r_id = hyperlink_el.get(qn("r:id"))
    if not r_id:
        return None
    try:
        return paragraph.part.rels[r_id].target_ref
    except (KeyError, AttributeError):
        return None


def extract_runs(paragraph: Paragraph) -> List[Run]:
    """
    Walk the paragraph's XML directly instead of using paragraph.runs.

    paragraph.runs ONLY returns <w:r> elements that are direct children
    of <w:p>. Any run wrapped in <w:hyperlink> (which is how every
    clickable phone/email/link in a resume or letterhead is stored in
    a normally-authored DOCX) is silently skipped by python-docx, so
    its text, style, and formatting never made it into the blueprint.

    Some converters — pdf2docx in particular — additionally write
    INVALID, reversed nesting: a <w:r> that itself contains a nested
    <w:hyperlink>, instead of the other way around. Both directions
    are handled below so hyperlink text is never silently dropped
    regardless of which tool produced the source DOCX.
    """
    runs: List[Run] = []

    def from_hyperlink(hyperlink_el):
        url = _hyperlink_url(paragraph, hyperlink_el)
        return [(r_el, url) for r_el in hyperlink_el.findall(qn("w:r"))]

    for child in paragraph._p:
        if child.tag == qn("w:r"):
            # Reversed/invalid nesting check: some converters put a
            # <w:hyperlink> INSIDE the run instead of around it.
            nested_hyperlink = child.find(qn("w:hyperlink"))
            if nested_hyperlink is not None:
                run_sources = from_hyperlink(nested_hyperlink)
            else:
                run_sources = [(child, None)]
        elif child.tag == qn("w:hyperlink"):
            run_sources = from_hyperlink(child)
        else:
            continue

        for r_el, hyperlink_url in run_sources:
            run = DocxRun(r_el, paragraph)
            runs.append(
                {
                    "text": run.text,
                    "style_id": (
                        run.style.style_id
                        if run.style
                        else None
                    ),
                    "style_name": (
                        run.style.name
                        if run.style
                        else None
                    ),
                    "bold": run.bold,
                    "italic": run.italic,
                    "underline": run.underline,
                    "font_name": run.font.name,
                    "font_size": (
                        run.font.size.pt
                        if run.font.size
                        else None
                    ),
                    "color": (
                        str(run.font.color.rgb)
                        if run.font.color
                        and run.font.color.rgb
                        else None
                    ),
                    "hyperlink_url": hyperlink_url,
                }
            )

    return runs


def _reconstruct_content(runs: List[Run]) -> str:
    """
    Build paragraph text from the extracted runs rather than
    paragraph.text, since paragraph.text has the same hyperlink
    blind spot as paragraph.runs.
    """
    return "".join(r["text"] or "" for r in runs)


def _line_spacing_data(fmt) -> dict[str, Any] | None:
    """
    Store line spacing as an explicit {value, unit, rule} triple.

    IMPORTANT: branch on fmt.line_spacing_rule, NOT on the Python type
    of fmt.line_spacing. python-docx's Length objects (returned when
    rule is EXACTLY or AT_LEAST) are a subclass of int, so a naive
    `isinstance(value, (int, float))` check matches them too and
    wrongly treats them as a bare multiplier — skipping the EMU-to-
    twips conversion and leaking a huge raw internal number (e.g.
    139700) downstream. That number then gets used as a line height
    directly, which is what was blowing up spacing and creating blank
    pages. Checking the rule first avoids this entirely.
    """
    value = fmt.line_spacing
    rule = fmt.line_spacing_rule

    if value is None:
        return None

    if rule in (WD_LINE_SPACING.EXACTLY, WD_LINE_SPACING.AT_LEAST):
        twips = getattr(value, "twips", None)
        if twips is None:
            return None
        return {
            "value": twips,
            "unit": "twips",
            "rule": "EXACTLY" if rule == WD_LINE_SPACING.EXACTLY else "AT_LEAST",
        }

    # MULTIPLE, SINGLE, ONE_POINT_FIVE, DOUBLE, or unset (defaults to
    # MULTIPLE): value is a plain multiplier here.
    return {
        "value": float(value),
        "unit": "multiplier",
        "rule": str(rule) if rule is not None else "MULTIPLE",
    }


def extract_paragraph_style(
    paragraph: Paragraph,
) -> ParagraphStyle:

    fmt = paragraph.paragraph_format
    p_pr = _child(paragraph._p, "w:pPr")

    return {
        "style_name": (
            paragraph.style.name
            if paragraph.style
            else None
        ),
        "style_id": (
            paragraph.style.style_id
            if paragraph.style
            else None
        ),
        "alignment": (
            str(paragraph.alignment)
            if paragraph.alignment is not None
            else None
        ),
        "space_before": (
            fmt.space_before.twips
            if fmt.space_before
            else None
        ),
        "space_after": (
            fmt.space_after.twips
            if fmt.space_after
            else None
        ),
        "line_spacing": _line_spacing_data(fmt),
        "left_indent": (
            fmt.left_indent.twips
            if fmt.left_indent
            else None
        ),
        "right_indent": (
            fmt.right_indent.twips
            if fmt.right_indent
            else None
        ),
        "first_line_indent": (
            fmt.first_line_indent.twips
            if fmt.first_line_indent
            else None
        ),
        "numbering": _numbering_data(paragraph),
        "tab_stops": _tab_stops(paragraph),
        "borders": _border_data(_child(p_pr, "w:pBdr")),
    }


def extract_paragraph_block(
    paragraph: Paragraph,
    block_id: str,
    order: int,
) -> DocumentBlock:

    image_slots = _image_slots(paragraph)
    runs = extract_runs(paragraph)

    return {
        "block_id": block_id,
        "order": order,
        "block_type": "heading"
        if paragraph.style
        and paragraph.style.name.startswith("Heading")
        else "paragraph",
        "content": _reconstruct_content(runs),

        "runs": runs,
        "paragraph_style": extract_paragraph_style(
            paragraph
        ),

        "table_data": None,
        "image_data": {
            "has_image": True,
            "slots": image_slots,
        } if image_slots else None,
        "image_slots": image_slots,
    }


def _grid_column_widths(table: Table) -> list[float | None] | None:
    tbl_grid = _child(table._tbl, "w:tblGrid")
    widths = [
        _twips_to_points(_attr(grid_col, "w:w"))
        for grid_col in _children(tbl_grid, "w:gridCol")
    ]
    return widths or None


def _row_height(row) -> dict[str, Any] | None:
    tr_pr = _child(row._tr, "w:trPr")
    height = _child(tr_pr, "w:trHeight")
    if height is None:
        return None
    return {
        "value": _twips_to_points(_attr(height, "w:val")),
        "rule": _attr(height, "w:hRule"),
    }


def _cell_margins(tc_pr) -> dict[str, float | None] | None:
    margin_el = _child(tc_pr, "w:tcMar")
    margins = {}
    for side in ("top", "left", "bottom", "right"):
        side_el = _child(margin_el, f"w:{side}")
        if side_el is not None:
            margins[side] = _twips_to_points(_attr(side_el, "w:w"))
    return margins or None


def _cell_grid_span(tc_pr) -> int | None:
    grid_span = _child(tc_pr, "w:gridSpan")
    value = _attr(grid_span, "w:val")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _cell_rowspan(tc_pr) -> str | None:
    v_merge = _child(tc_pr, "w:vMerge")
    if v_merge is None:
        return None
    return _attr(v_merge, "w:val") or "continue"


def _cell_data(cell: _Cell) -> dict[str, Any]:
    tc_pr = _child(cell._tc, "w:tcPr")
    width_el = _child(tc_pr, "w:tcW")
    v_align = _child(tc_pr, "w:vAlign")

    return {
        "text": cell.text,
        "width": _twips_to_points(_attr(width_el, "w:w")),
        "width_type": _attr(width_el, "w:type"),
        "colspan": _cell_grid_span(tc_pr),
        "rowspan": _cell_rowspan(tc_pr),
        "margins": _cell_margins(tc_pr),
        "vertical_alignment": _attr(v_align, "w:val"),
        "borders": _border_data(_child(tc_pr, "w:tcBorders")),
        "shading": _shading_data(tc_pr),
    }


def _looks_like_layout_table(rows: list, borders: dict | None) -> bool:
    """
    Heuristic flag for tables that are really a single justified text
    line (e.g. "Job Title ......... Location") misread as a table by
    PDF-to-DOCX conversion, rather than genuine tabular data. This is
    common with pdf2docx output specifically. It doesn't change how
    the table is stored, only tags it so the generation step can treat
    it as plain aligned text with tab stops instead of forcing it into
    a rigid grid that risks overflow when values are replaced with
    longer/shorter data.

    Signals: exactly one row, 2-3 columns, and no real grid lines on
    the sides/inside (a genuine data table almost always has full
    borders or shading; a converted text line typically has at most a
    single top rule, if anything).
    """
    if len(rows) != 1:
        return False

    cell_count = len(rows[0]["cells"])
    if cell_count not in (2, 3):
        return False

    if not borders:
        return True

    has_grid_lines = any(
        side in borders for side in ("insideH", "insideV", "left", "right", "bottom")
    )
    return not has_grid_lines


def extract_table_block(
    table: Table,
    block_id: str,
    order: int,
) -> DocumentBlock:

    rows = []
    structured_rows = []

    for row in table.rows:
        row_data = []
        structured_cells = []

        for cell in row.cells:
            row_data.append(cell.text)
            structured_cells.append(_cell_data(cell))

        rows.append({"cells": row_data})
        structured_rows.append(
            {
                "height": _row_height(row),
                "cells": structured_cells,
            }
        )

    tbl_pr = _child(table._tbl, "w:tblPr")
    borders = _border_data(_child(tbl_pr, "w:tblBorders"))

    return {
        "block_id": block_id,
        "order": order,
        "block_type": "table",
        "content": None,
        "role": None,
        "editable": False,

        "runs": None,
        "paragraph_style": None,

        "table_data": {
            "rows": rows,
            "structured_rows": structured_rows,
            "column_widths": _grid_column_widths(table),
            "borders": borders,
            "shading": _shading_data(tbl_pr),
            "is_likely_layout_table": _looks_like_layout_table(rows, borders),
        },

        "image_data": None,
        "image_slots": None,
    }


def extract_image_block(
    image_name: str,
    relationship_id: str | None,
    block_id: str,
    order: int,
) -> DocumentBlock:

    return {
        "block_id": block_id,
        "order": order,
        "block_type": "image",
        "content": None,
        "role": None,
        "editable": False,

        "runs": None,
        "paragraph_style": None,

        "table_data": None,

        "image_data": {
            "has_image": True,
            "name": image_name,
            "relationship_id": relationship_id,
        },
        "image_slots": [
            {
                "has_image": True,
                "relationship_id": relationship_id,
                "name": image_name,
                "width": None,
                "height": None,
            }
        ],
    }