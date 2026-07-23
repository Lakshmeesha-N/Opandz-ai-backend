from typing import TypedDict, List, Optional, Literal


class Border(TypedDict):
    value: Optional[str]
    size: Optional[int]
    space: Optional[int]
    color: Optional[str]


class Shading(TypedDict):
    fill: Optional[str]
    color: Optional[str]
    value: Optional[str]


class Numbering(TypedDict):
    num_id: Optional[str]
    level: Optional[str]
    list_type: Optional[str]
    # Resolved from numbering.xml by NumberingResolver (Fix 4)
    num_fmt: Optional[str]   # e.g. "bullet", "decimal", "lowerLetter"
    lvl_text: Optional[str]  # e.g. "•", "%1.", "(%1)"
    start: Optional[int]     # starting value for the level


class TabStop(TypedDict):
    position: Optional[float]
    alignment: Optional[str]
    leader: Optional[str]


class ImageSlot(TypedDict):
    has_image: bool
    relationship_id: Optional[str]
    name: Optional[str]
    width: Optional[float]
    height: Optional[float]


# --------------------------
# Run level formatting
# --------------------------

class Run(TypedDict):
    text: str
    style_id: Optional[str]
    style_name: Optional[str]
    bold: Optional[bool]
    italic: Optional[bool]
    underline: Optional[bool]
    font_name: Optional[str]
    font_size: Optional[float]
    color: Optional[str]
    # Resolved target URL when this run came from a <w:hyperlink> —
    # normal nesting (hyperlink wraps run) or pdf2docx's reversed
    # nesting (run wraps hyperlink). None for plain, non-linked runs.
    hyperlink_url: Optional[str]
    # Resolved from theme XML by ThemeResolver (Fix 6)
    # theme_color is the OOXML slot name (e.g. "accent1") when the
    # concrete `color` was derived from the theme rather than an explicit RGB.
    theme_color: Optional[str]
    # theme_font is the w:asciiTheme / w:hAnsiTheme slot (e.g. "majorAscii")
    # when font_name was derived from the theme rather than an explicit name.
    theme_font: Optional[str]


# --------------------------
# Line spacing
# --------------------------

class LineSpacing(TypedDict):
    # Meaning of `value` depends on `unit`:
    #   unit == "multiplier" -> value is a bare multiplier (1.0 = single)
    #   unit == "twips"      -> value is an absolute twips length
    # `rule` mirrors python-docx's WD_LINE_SPACING: MULTIPLE, SINGLE,
    # ONE_POINT_FIVE, DOUBLE, EXACTLY, AT_LEAST.
    value: float
    unit: Literal["multiplier", "twips"]
    rule: str


# --------------------------
# Paragraph formatting
# --------------------------

class ParagraphStyle(TypedDict):
    style_name: Optional[str]
    style_id: Optional[str]
    alignment: Optional[str]

    space_before: Optional[float]
    space_after: Optional[float]
    line_spacing: Optional[LineSpacing]

    left_indent: Optional[float]
    right_indent: Optional[float]
    first_line_indent: Optional[float]

    numbering: Optional[Numbering]
    tab_stops: Optional[List[TabStop]]
    borders: Optional[dict[str, Border]]


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

    # Content used by AI. All three are always present on every block
    # returned by block_extractor.py (paragraph blocks set content and
    # leave role/editable as None/False; table and image blocks set
    # role/editable and leave content as None) — kept un-commented so
    # nothing downstream that filters strictly by this schema silently
    # drops them.
    content: Optional[str]
    role: Optional[str]
    editable: bool

    # Text formatting
    runs: Optional[List[Run]]
    paragraph_style: Optional[ParagraphStyle]

    # Complex objects
    table_data: Optional[dict]
    image_data: Optional[dict]
    image_slots: Optional[List[ImageSlot]]


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
    section_break_type: Optional[str]
    header_linked_to_previous: Optional[bool]
    footer_linked_to_previous: Optional[bool]


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