from typing import TypedDict, List, Optional, Literal


# --------------------------
# Run level formatting
# --------------------------

class Run(TypedDict):
    text: str
    bold: Optional[bool]
    italic: Optional[bool]
    underline: Optional[bool]
    font_name: Optional[str]
    font_size: Optional[float]
    color: Optional[str]


# --------------------------
# Paragraph formatting
# --------------------------

class ParagraphStyle(TypedDict):
    style_name: Optional[str]
    alignment: Optional[str]

    space_before: Optional[float]
    space_after: Optional[float]
    line_spacing: Optional[float]

    left_indent: Optional[float]
    right_indent: Optional[float]
    first_line_indent: Optional[float]


# --------------------------
# Generic document block
# --------------------------

class DocumentBlock(TypedDict):
    block_id: str
    order: int

    block_type: Literal[
        "paragraph",
        "heading",
        "table",
        "image"
    ]

    # Content used by AI
    #content: Optional[str]
    #role: Optional[str]
    #editable: bool

    # Text formatting
    runs: Optional[List[Run]]
    paragraph_style: Optional[ParagraphStyle]

    # Complex objects
    table_data: Optional[dict]
    image_data: Optional[dict]


# --------------------------
# Section page properties
# --------------------------

class SectionMetadata(TypedDict):
    page_width: Optional[float]
    page_height: Optional[float]

    margin_top: Optional[float]
    margin_bottom: Optional[float]
    margin_left: Optional[float]
    margin_right: Optional[float]

    orientation: Optional[str]


# --------------------------
# DOCX Section
# --------------------------

class DocumentSection(TypedDict):
    section_id: str

    # Page layout for this section
    metadata: SectionMetadata

    # Repeated content
    header_blocks: List[DocumentBlock]

    # Actual document content
    body_blocks: List[DocumentBlock]

    # Repeated content
    footer_blocks: List[DocumentBlock]


# --------------------------
# Entire document
# --------------------------

class DocumentBlueprint(TypedDict):
    title: str

    sections: List[DocumentSection]