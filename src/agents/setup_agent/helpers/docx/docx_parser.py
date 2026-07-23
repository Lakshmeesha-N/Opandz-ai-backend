# docx_parser.py

from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.ns import qn

try:
    from src.agents.setup_agent.schema.docx_schema import (
        DocumentBlueprint,
        DocumentSection,
        SectionMetadata,
    )
    from src.agents.setup_agent.helpers.docx.section_splitter import (
        split_body_by_sections,
    )
    from src.agents.setup_agent.helpers.docx.block_extractor import (
        extract_paragraph_block,
        extract_table_block,
    )
    from src.agents.setup_agent.helpers.docx.numbering_resolver import NumberingResolver
    from src.agents.setup_agent.helpers.docx.theme_resolver import ThemeResolver

except ModuleNotFoundError:
    import os
    import sys

    # When running this file directly (python docx_parser.py) the
    # top-level package `src` may not be on sys.path. Add the project
    # root (parent of `src`) so absolute imports work.
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../..")
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from src.agents.setup_agent.schema.docx_schema import (
        DocumentBlueprint,
        DocumentSection,
        SectionMetadata,
    )
    from src.agents.setup_agent.helpers.docx.section_splitter import (
        split_body_by_sections,
    )
    from src.agents.setup_agent.helpers.docx.block_extractor import (
        extract_paragraph_block,
        extract_table_block,
    )
    from src.agents.setup_agent.helpers.docx.numbering_resolver import NumberingResolver
    from src.agents.setup_agent.helpers.docx.theme_resolver import ThemeResolver


def _remove_none(obj):
    """Recursively remove keys with None values from dicts/lists."""
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if v is None:
                continue
            new[k] = _remove_none(v)
        return new
    if isinstance(obj, list):
        return [
            _remove_none(v) if v is not None else v
            for v in obj
        ]
    return obj


def extract_xml_blocks(elements, doc, numbering_resolver=None, theme_resolver=None):
    """
    Convert XML elements of a section into DocumentBlocks.
    Both resolvers are optional; passing None gives the same behaviour as
    the old code (graceful fallback).
    """
    blocks = []
    order = 0

    for element in elements:

        if element.tag == qn("w:p"):
            paragraph = Paragraph(element, doc)
            blocks.append(
                extract_paragraph_block(
                    paragraph,
                    f"block_{order}",
                    order,
                    numbering_resolver=numbering_resolver,
                    theme_resolver=theme_resolver,
                )
            )
            order += 1

        elif element.tag == qn("w:tbl"):
            table = Table(element, doc)
            blocks.append(
                extract_table_block(
                    table,
                    f"block_{order}",
                    order,
                )
            )
            order += 1

    return blocks


def extract_section_metadata(section) -> SectionMetadata:
    """
    Extract page properties of a DOCX section.
    """
    return {
        "page_width": (
            section.page_width.twips
            if section.page_width
            else None
        ),
        "page_height": (
            section.page_height.twips
            if section.page_height
            else None
        ),
        "margin_top": (
            section.top_margin.twips
            if section.top_margin
            else None
        ),
        "margin_bottom": (
            section.bottom_margin.twips
            if section.bottom_margin
            else None
        ),
        "margin_left": (
            section.left_margin.twips
            if section.left_margin
            else None
        ),
        "margin_right": (
            section.right_margin.twips
            if section.right_margin
            else None
        ),
        "orientation": (
            str(section.orientation)
            if section.orientation is not None
            else None
        ),
        "section_break_type": (
            str(section.start_type)
            if section.start_type is not None
            else None
        ),
        "header_linked_to_previous": section.header.is_linked_to_previous,
        "footer_linked_to_previous": section.footer.is_linked_to_previous,
    }


def parse_docx(file_path: str) -> DocumentBlueprint:
    """
    Main DOCX → DocumentBlueprint parser.
    """

    doc = Document(file_path)

    # Build resolvers once for the whole document
    numbering_resolver = NumberingResolver(doc)
    theme_resolver = ThemeResolver(doc)

    # Split body based on actual DOCX section breaks
    body_sections = split_body_by_sections(doc.element.body)

    sections = []

    for index, section in enumerate(doc.sections):

        # Header — resolvers passed through for consistent run extraction
        header_blocks = [
            extract_paragraph_block(
                para,
                f"header_{i}",
                i,
                numbering_resolver=numbering_resolver,
                theme_resolver=theme_resolver,
            )
            for i, para in enumerate(section.header.paragraphs)
        ]

        # Body
        body_blocks = extract_xml_blocks(
            body_sections[index],
            doc,
            numbering_resolver=numbering_resolver,
            theme_resolver=theme_resolver,
        )

        # Footer
        footer_blocks = [
            extract_paragraph_block(
                para,
                f"footer_{i}",
                i,
                numbering_resolver=numbering_resolver,
                theme_resolver=theme_resolver,
            )
            for i, para in enumerate(section.footer.paragraphs)
        ]

        document_section: DocumentSection = {
            "section_id": f"section_{index + 1}",
            "metadata": extract_section_metadata(section),
            "header_blocks": header_blocks,
            "body_blocks": body_blocks,
            "footer_blocks": footer_blocks,
        }

        sections.append(document_section)

    blueprint: DocumentBlueprint = {
        "title": file_path.split("\\")[-1],
        "sections": sections,
    }

    # Single post-pass to remove None-valued keys across the whole blueprint
    return _remove_none(blueprint)


if __name__ == "__main__":
    # Example usage
    file_path = "test/Test_file.docx"
    blueprint = parse_docx(file_path)
    import json
    json.dump(blueprint, open("test/Test_file_blueprint_none_rm.json", "w"), indent=2)
    print(json.dumps(blueprint, indent=2))
