# block_extractor.py

from typing import Any, List
from docx.text.paragraph import Paragraph
from docx.table import Table, _Cell
from docx.oxml.ns import qn

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


def extract_runs(paragraph: Paragraph) -> List[Run]:
    runs: List[Run] = []

    for run in paragraph.runs:
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
            }
        )

    return runs


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
            fmt.space_before.pt
            if fmt.space_before
            else None
        ),
        "space_after": (
            fmt.space_after.pt
            if fmt.space_after
            else None
        ),
        "line_spacing": (
            float(fmt.line_spacing)
            if isinstance(
                fmt.line_spacing,
                (int, float),
            )
            else None
        ),
        "left_indent": (
            fmt.left_indent.pt
            if fmt.left_indent
            else None
        ),
        "right_indent": (
            fmt.right_indent.pt
            if fmt.right_indent
            else None
        ),
        "first_line_indent": (
            fmt.first_line_indent.pt
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

    return {
        "block_id": block_id,
        "order": order,
        "block_type": "heading"
        if paragraph.style
        and paragraph.style.name.startswith("Heading")
        else "paragraph",
        "content": paragraph.text,

        "runs": extract_runs(paragraph),
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
            "borders": _border_data(_child(tbl_pr, "w:tblBorders")),
            "shading": _shading_data(tbl_pr),
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
