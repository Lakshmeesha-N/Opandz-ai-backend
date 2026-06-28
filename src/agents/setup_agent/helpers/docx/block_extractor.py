# block_extractor.py

from typing import List
from docx.text.paragraph import Paragraph
from docx.table import Table

from src.agents.setup_agent.schema.docx_schema import (
    Run,
    ParagraphStyle,
    DocumentBlock,
)


def extract_runs(paragraph: Paragraph) -> List[Run]:
    runs: List[Run] = []

    for run in paragraph.runs:
        runs.append(
            {
                "text": run.text,
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

    return {
        "style_name": (
            paragraph.style.name
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
    }


def extract_paragraph_block(
    paragraph: Paragraph,
    block_id: str,
    order: int,
) -> DocumentBlock:

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
        "image_data": None,
    }


def extract_table_block(
    table: Table,
    block_id: str,
    order: int,
) -> DocumentBlock:

    rows = []

    for row in table.rows:
        row_data = []

        for cell in row.cells:
            row_data.append(cell.text)

        rows.append(row_data)

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
            "rows": rows
        },

        "image_data": None,
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
            "name": image_name,
            "relationship_id": relationship_id,
        },
    }