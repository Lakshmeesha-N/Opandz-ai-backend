# block_extractor.py

from __future__ import annotations

from typing import Any, List, Optional
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

# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Border / shading helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# FIX 4 — Numbering data (uses NumberingResolver when available)
# ---------------------------------------------------------------------------

def _numbering_data(
    paragraph: Paragraph,
    numbering_resolver=None,
) -> dict[str, Any] | None:
    """
    Extract numPr and, when a NumberingResolver is supplied, cross-reference
    numbering.xml to get the real numFmt / lvlText so list_type is correct.
    """
    p_pr = _child(paragraph._p, "w:pPr")
    num_pr = _child(p_pr, "w:numPr")

    if num_pr is None:
        return None

    num_id_el = _child(num_pr, "w:numId")
    level_el = _child(num_pr, "w:ilvl")
    num_id = _attr(num_id_el, "w:val")
    level = _attr(level_el, "w:val")

    # FIX 3 — use resolver, not style-name string heuristic
    if numbering_resolver is not None:
        list_type = numbering_resolver.list_type(num_id, level)
        resolved = numbering_resolver.resolve(num_id, level)
    else:
        list_type = "numbered"  # safe fallback (numPr exists)
        resolved = None

    result: dict[str, Any] = {
        "num_id": num_id,
        "level": level,
        "list_type": list_type,
    }

    # FIX 4 — attach resolved lvlText / numFmt when available
    if resolved:
        if resolved.get("num_fmt") is not None:
            result["num_fmt"] = resolved["num_fmt"]
        if resolved.get("lvl_text") is not None:
            result["lvl_text"] = resolved["lvl_text"]
        if resolved.get("start") is not None:
            result["start"] = resolved["start"]

    return result


# ---------------------------------------------------------------------------
# Tab stops
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Image slots
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Hyperlink URL resolver
# ---------------------------------------------------------------------------

def _hyperlink_url(paragraph: Paragraph, hyperlink_el) -> str | None:
    """Resolve hyperlink relationship to target URL."""
    r_id = hyperlink_el.get(qn("r:id"))
    if not r_id:
        return None
    try:
        if hasattr(paragraph.part, "rels") and r_id in paragraph.part.rels:
            return paragraph.part.rels[r_id].target_ref
        return None
    except (KeyError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# FIX 1 — Run extraction: recurse into w:ins / w:del / w:sdt
# ---------------------------------------------------------------------------

# Tags that wrap runs without contributing text themselves
_TRANSPARENT_WRAPPERS = frozenset([
    qn("w:ins"),          # tracked insertion
    qn("w:del"),          # tracked deletion (w:delText carries the text)
    qn("w:moveFrom"),     # tracked move-source
    qn("w:moveTo"),       # tracked move-destination
    qn("w:sdtContent"),   # content-control inner content
])


def _iter_run_elements(element, paragraph: Paragraph):
    """
    Recursively yield (r_element, hyperlink_url_or_None) for every w:r
    contained within *element*, descending transparently into:
      - w:ins, w:del, w:moveFrom, w:moveTo  (tracked changes)
      - w:sdt / w:sdtContent                (content controls)
      - w:hyperlink                          (hyperlinks at any depth)
    """
    for child in element:
        tag = child.tag

        if tag == qn("w:r"):
            yield child, None

        elif tag == qn("w:hyperlink"):
            url = _hyperlink_url(paragraph, child)
            # Recurse into hyperlink to catch its w:r children (and nested wrappers)
            for r_el, _ in _iter_run_elements(child, paragraph):
                yield r_el, url

        elif tag == qn("w:sdt"):
            # w:sdt → w:sdtContent → runs
            sdt_content = child.find(qn("w:sdtContent"))
            if sdt_content is not None:
                yield from _iter_run_elements(sdt_content, paragraph)

        elif tag in _TRANSPARENT_WRAPPERS:
            yield from _iter_run_elements(child, paragraph)


def extract_runs(paragraph: Paragraph, theme_resolver=None) -> List[Run]:
    """
    Extract every run in the paragraph, including runs nested inside
    tracked-change wrappers (w:ins, w:del) and content controls (w:sdt).

    FIX 6: When a theme_resolver is available, resolve theme colors and
    theme font names to their concrete values.
    """
    runs: List[Run] = []

    for r_el, hyperlink_url in _iter_run_elements(paragraph._p, paragraph):
        try:
            run = DocxRun(r_el, paragraph)
            text = run.text or ""

            # --- color resolution (FIX 6) ---
            color: str | None = None
            theme_color: str | None = None

            try:
                if run.font.color and run.font.color.rgb:
                    color = str(run.font.color.rgb)
                elif theme_resolver is not None and run.font.color:
                    tc = run.font.color.theme_color  # may be None
                    brightness = run.font.color.brightness  # may be None or 0.0
                    if tc is not None:
                        resolved_hex = theme_resolver.resolve_color(tc, brightness)
                        if resolved_hex:
                            color = resolved_hex
                            theme_color = str(tc)
            except Exception:
                pass

            # --- font name resolution (FIX 6) ---
            font_name: str | None = None
            theme_font: str | None = None

            try:
                font_name = run.font.name  # explicit name or None
                if font_name is None and theme_resolver is not None:
                    # Check w:rFonts asciiTheme / hAnsiTheme
                    r_pr = _child(r_el, "w:rPr")
                    r_fonts = _child(r_pr, "w:rFonts")
                    if r_fonts is not None:
                        for attr_name in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme"):
                            slot = _attr(r_fonts, attr_name)
                            if slot:
                                resolved_font = theme_resolver.resolve_font(slot)
                                if resolved_font:
                                    font_name = resolved_font
                                    theme_font = slot
                                break
            except Exception:
                pass

            # --- font size ---
            try:
                font_size = run.font.size.pt if run.font.size else None
            except Exception:
                font_size = None

            runs.append(
                {
                    "text": text,
                    "style_id": run.style.style_id if run.style else None,
                    "style_name": run.style.name if run.style else None,
                    "bold": run.bold,
                    "italic": run.italic,
                    "underline": run.underline,
                    "font_name": font_name,
                    "font_size": font_size,
                    "color": color,
                    "theme_color": theme_color,
                    "theme_font": theme_font,
                    "hyperlink_url": hyperlink_url,
                }
            )
        except Exception:
            continue

    return runs


# ---------------------------------------------------------------------------
# Reconstruct paragraph text from runs
# ---------------------------------------------------------------------------

def _reconstruct_content(runs: List[Run]) -> str:
    if not runs:
        return ""
    return "".join(str(r.get("text", "")) or "" for r in runs if r is not None)


# ---------------------------------------------------------------------------
# FIX 2 — Line spacing: rule-driven, read directly from XML
# ---------------------------------------------------------------------------

def _line_spacing_data(fmt) -> dict[str, Any] | None:
    """
    Read line spacing directly from the paragraph XML (<w:spacing> element)
    so we never depend on python-docx's type coercion.

    w:lineRule values:
      "auto"    → multiplier (value is 240 = single, 360 = 1.5x, etc.)
      "exact"   → twips (WD_LINE_SPACING.EXACTLY)
      "atLeast" → twips (WD_LINE_SPACING.AT_LEAST)
      absent    → treat as "auto"

    We keep fmt as a parameter so callers can pass paragraph_format;
    but we reach into the underlying XML for the raw values.
    """
    if fmt is None:
        return None

    # Access the underlying pPr/spacing element from python-docx's format object
    # paragraph_format._pPr is the <w:pPr> element; may be None for default-only paras
    try:
        p_pr = fmt._pPr  # type: ignore[attr-defined]
    except AttributeError:
        return None

    if p_pr is None:
        return None

    spacing_el = p_pr.find(qn("w:spacing"))
    if spacing_el is None:
        return None

    line_val = spacing_el.get(qn("w:line"))
    line_rule = spacing_el.get(qn("w:lineRule"))  # "auto" | "exact" | "atLeast" | None

    if line_val is None:
        return None

    try:
        raw = int(line_val)
    except (TypeError, ValueError):
        return None

    # FIX 2 — determine unit purely from lineRule, not from magnitude
    if line_rule in ("exact", "atLeast"):
        return {
            "value": raw,                           # twips
            "unit": "twips",
            "rule": "EXACTLY" if line_rule == "exact" else "AT_LEAST",
        }
    else:
        # "auto" or absent → value is in 240ths of a line (single = 240)
        return {
            "value": raw / 240.0,                   # normalise to multiplier
            "unit": "multiplier",
            "rule": "MULTIPLE",
        }


# ---------------------------------------------------------------------------
# FIX 5 — Style inheritance: walk basedOn chain for effective values
# ---------------------------------------------------------------------------

def _walk_style_chain(style):
    """Yield style and every ancestor via basedOn, stopping at cycles."""
    seen = set()
    current = style
    while current is not None:
        style_id = getattr(current, "style_id", None)
        if style_id in seen:
            break
        seen.add(style_id)
        yield current
        current = getattr(current, "base_style", None)


def _effective_paragraph_fmt_xml(paragraph: Paragraph):
    """
    Walk the paragraph's style chain and collect the first non-None value for
    each spacing/indent attribute from the XML <w:pPr> of each style.

    Returns a dict of raw XML values: space_before, space_after, left_indent,
    right_indent, first_line_indent (all in twips as str), alignment (str).
    """
    # Attributes: (result_key, spacing_xml_attr, spacing_element)
    SPACING_ATTRS = [
        ("space_before", "w:before", "spacing"),
        ("space_after",  "w:after",  "spacing"),
    ]
    INDENT_ATTRS = [
        ("left_indent",       "w:left",  "ind"),
        ("right_indent",      "w:right", "ind"),
        ("first_line_indent", "w:firstLine", "ind"),
    ]

    result: dict[str, str | None] = {
        "space_before": None,
        "space_after": None,
        "left_indent": None,
        "right_indent": None,
        "first_line_indent": None,
        "alignment": None,
        "line_spacing_raw": None,  # ("value_str", "lineRule_str") tuple stored as list
    }

    # Collect sources: paragraph-level pPr first, then style chain
    def _ppr_sources():
        # 1. paragraph's own pPr
        p_el = paragraph._p
        own_ppr = p_el.find(qn("w:pPr"))
        if own_ppr is not None:
            yield own_ppr
        # 2. walk style chain
        for style in _walk_style_chain(paragraph.style):
            try:
                style_el = style.element  # type: ignore[attr-defined]
                ppr = style_el.find(qn("w:pPr"))
                if ppr is not None:
                    yield ppr
            except AttributeError:
                continue

    for ppr in _ppr_sources():
        # spacing element
        spacing = ppr.find(qn("w:spacing"))
        if spacing is not None:
            if result["space_before"] is None:
                result["space_before"] = spacing.get(qn("w:before"))
            if result["space_after"] is None:
                result["space_after"] = spacing.get(qn("w:after"))
            if result["line_spacing_raw"] is None:
                line_val = spacing.get(qn("w:line"))
                line_rule = spacing.get(qn("w:lineRule"))
                if line_val is not None:
                    result["line_spacing_raw"] = [line_val, line_rule]

        # indent element
        ind = ppr.find(qn("w:ind"))
        if ind is not None:
            if result["left_indent"] is None:
                result["left_indent"] = ind.get(qn("w:left"))
            if result["right_indent"] is None:
                result["right_indent"] = ind.get(qn("w:right"))
            if result["first_line_indent"] is None:
                result["first_line_indent"] = ind.get(qn("w:firstLine"))

        # alignment (jc)
        jc = ppr.find(qn("w:jc"))
        if jc is not None and result["alignment"] is None:
            result["alignment"] = jc.get(qn("w:val"))

        # Early exit if all found
        if all(v is not None for v in result.values()):
            break

    return result


def _line_spacing_from_raw(raw_pair: list | None) -> dict[str, Any] | None:
    """Convert the [line_val, line_rule] pair from _effective_paragraph_fmt_xml."""
    if raw_pair is None:
        return None
    line_val, line_rule = raw_pair[0], raw_pair[1]
    try:
        raw = int(line_val)
    except (TypeError, ValueError):
        return None

    if line_rule in ("exact", "atLeast"):
        return {
            "value": raw,
            "unit": "twips",
            "rule": "EXACTLY" if line_rule == "exact" else "AT_LEAST",
        }
    else:
        return {
            "value": raw / 240.0,
            "unit": "multiplier",
            "rule": "MULTIPLE",
        }


# ---------------------------------------------------------------------------
# Paragraph style extractor (uses all fixes)
# ---------------------------------------------------------------------------

def extract_paragraph_style(
    paragraph: Paragraph,
    numbering_resolver=None,
    theme_resolver=None,
) -> ParagraphStyle:
    p_pr = _child(paragraph._p, "w:pPr")

    # FIX 5: get effective values by walking the style inheritance chain
    eff = _effective_paragraph_fmt_xml(paragraph)

    def _twips(val: str | None) -> float | None:
        return int(val) / 20 if val is not None and val.lstrip("-").isdigit() else None

    # Alignment: prefer python-docx (handles enum nicely), fall back to XML
    alignment: str | None
    if paragraph.alignment is not None:
        alignment = str(paragraph.alignment)
    elif eff["alignment"] is not None:
        alignment = eff["alignment"]
    else:
        alignment = None

    return {
        "style_name": paragraph.style.name if paragraph.style else None,
        "style_id": paragraph.style.style_id if paragraph.style else None,
        "alignment": alignment,
        # FIX 5: inherited values from basedOn chain
        "space_before": _twips(eff["space_before"]),
        "space_after":  _twips(eff["space_after"]),
        "line_spacing": _line_spacing_from_raw(eff["line_spacing_raw"]),  # FIX 2 + 5
        "left_indent":       _twips(eff["left_indent"]),
        "right_indent":      _twips(eff["right_indent"]),
        "first_line_indent": _twips(eff["first_line_indent"]),
        # FIX 3 + 4: numbering via resolver
        "numbering": _numbering_data(paragraph, numbering_resolver),
        "tab_stops": _tab_stops(paragraph),
        "borders": _border_data(_child(p_pr, "w:pBdr")),
    }


# ---------------------------------------------------------------------------
# Paragraph block extractor
# ---------------------------------------------------------------------------

def extract_paragraph_block(
    paragraph: Paragraph,
    block_id: str,
    order: int,
    numbering_resolver=None,
    theme_resolver=None,
) -> DocumentBlock:
    image_slots = _image_slots(paragraph)
    # FIX 1 + 6: runs now include tracked-change text and theme color/font
    runs = extract_runs(paragraph, theme_resolver=theme_resolver)

    return {
        "block_id": block_id,
        "order": order,
        "block_type": (
            "heading"
            if paragraph.style and paragraph.style.name.startswith("Heading")
            else "paragraph"
        ),
        "content": _reconstruct_content(runs),
        "runs": runs,
        "paragraph_style": extract_paragraph_style(
            paragraph,
            numbering_resolver=numbering_resolver,
            theme_resolver=theme_resolver,
        ),
        "table_data": None,
        "image_data": {"has_image": True, "slots": image_slots} if image_slots else None,
        "image_slots": image_slots,
    }


# ---------------------------------------------------------------------------
# Table helpers (unchanged)
# ---------------------------------------------------------------------------

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