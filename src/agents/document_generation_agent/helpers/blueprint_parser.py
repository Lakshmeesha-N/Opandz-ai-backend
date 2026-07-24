# src/agents/document_generation_agent/helpers/blueprint_parser.py

import re
import logging

logger = logging.getLogger(__name__)


def _to_snake_case(text: str) -> str:
    """Convert section heading text to a valid snake_case function name suffix."""
    # Remove leading numbers like "1." or "14 (a)" → keep alphanumeric
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", "_", text.strip().lower())
    text = re.sub(r"_+", "_", text)
    return text[:60].strip("_")


def parse_blueprint_sections(blueprint_markdown: str) -> dict:
    """
    Split blueprint_markdown (a single string with ## Section Name headers)
    into:
      - metadata: str   — page setup, fonts, colors, named styles, numbering
      - sections: list  — [{index, name, fn_name, markdown, is_header, is_footer}]

    The blueprint format (from the setup agent) is:
      [preamble] ## 1. Page Setup ... ## 2. Fonts ... ## 3. Font Sizes ...
      ... ## 6. Numbering ...
      ## Section Name  (semantic label)
      ## Original Content [N]  (verbatim document text)
      ## Formatting Blueprint  (styling rules)
      [repeating triplets]
    """
    if not blueprint_markdown or not blueprint_markdown.strip():
        logger.warning("[blueprint_parser] Empty blueprint_markdown received")
        return {"metadata": "", "sections": []}

    # Split on "## " — every chunk is one ## block
    raw_parts = re.split(r"##\s+", blueprint_markdown)

    # Separate metadata (numbered system sections) from content triplets
    metadata_chunks: list[str] = []
    content_parts: list[str] = []
    reached_content = False

    for i, part in enumerate(raw_parts):
        stripped = part.strip()
        if not stripped:
            continue

        first_line = stripped.split("\n")[0].strip()

        # Metadata sections: "Blueprint Metadata", "1. Page Setup", "2. Fonts", etc.
        is_numbered_meta = bool(re.match(r"^\d+\.\s+", first_line))
        is_blueprint_meta = "Blueprint Metadata" in first_line
        is_original_content = first_line.startswith("Original Content")
        is_formatting_blueprint = first_line.startswith("Formatting Blueprint")

        if not reached_content and (is_blueprint_meta or is_numbered_meta):
            metadata_chunks.append(f"## {stripped}")
            continue

        # Once we hit the first Original Content or a named section that precedes
        # content — we are in body territory
        if is_original_content or is_formatting_blueprint:
            reached_content = True
        elif not reached_content:
            # Check if the NEXT part is an Original Content → this is a section name
            # We'll collect it as content territory
            reached_content = True

        content_parts.append(stripped)

    metadata_md = "\n\n".join(metadata_chunks)

    # ── Parse content_parts into (name, content, formatting) triplets ──
    sections: list[dict] = []
    section_counter = 0
    i = 0

    while i < len(content_parts):
        part = content_parts[i].strip()
        if not part:
            i += 1
            continue

        first_line = part.split("\n")[0].strip()

        # ── Case A: Named section (not OC, not FB) ──
        if (not first_line.startswith("Original Content")
                and not first_line.startswith("Formatting Blueprint")):

            name = first_line
            content_text = ""
            format_text = ""

            # Look ahead for OC block
            j = i + 1
            if j < len(content_parts):
                next_first = content_parts[j].split("\n")[0].strip()
                if next_first.startswith("Original Content"):
                    # Strip prefix "Original Content [N]"
                    raw_oc = content_parts[j].strip()
                    content_text = re.sub(r"^Original Content\s*\d*\s*", "", raw_oc, count=1).strip()
                    j += 1

            # Look ahead for FB block
            if j < len(content_parts):
                next_first = content_parts[j].split("\n")[0].strip()
                if next_first.startswith("Formatting Blueprint"):
                    raw_fb = content_parts[j].strip()
                    format_text = re.sub(r"^Formatting Blueprint\s*", "", raw_fb, count=1).strip()
                    j += 1

            section_counter += 1
            _append_section(sections, section_counter, name, content_text, format_text)
            i = j

        # ── Case B: Orphaned Original Content (no preceding name) ──
        elif first_line.startswith("Original Content"):
            raw_oc = part
            content_text = re.sub(r"^Original Content\s*\d*\s*", "", raw_oc, count=1).strip()
            format_text = ""

            j = i + 1
            if j < len(content_parts):
                next_first = content_parts[j].split("\n")[0].strip()
                if next_first.startswith("Formatting Blueprint"):
                    raw_fb = content_parts[j].strip()
                    format_text = re.sub(r"^Formatting Blueprint\s*", "", raw_fb, count=1).strip()
                    j += 1

            # Auto-name from first meaningful words of content
            first_words = " ".join(content_text.split()[:6])
            auto_name = first_words if first_words else f"Section {section_counter + 1}"

            section_counter += 1
            _append_section(sections, section_counter, auto_name, content_text, format_text)
            i = j

        # ── Case C: Orphaned Formatting Blueprint ── skip
        else:
            i += 1

    logger.info(
        "[blueprint_parser] Parsed %d sections from blueprint (%d metadata chars)",
        len(sections),
        len(metadata_md),
    )
    return {"metadata": metadata_md, "sections": sections}


def _append_section(
    sections: list,
    index: int,
    name: str,
    content_text: str,
    format_text: str,
) -> None:
    """Build a section dict and append to sections list."""
    lower = name.lower()
    is_header = any(k in lower for k in ("header", "running header", "page header"))
    is_footer = any(k in lower for k in ("footer", "page footer", "running footer"))

    if is_header:
        fn_name = "build_section_header"
    elif is_footer:
        fn_name = "build_section_footer"
    else:
        fn_name = f"build_{index:02d}_{_to_snake_case(name)}"

    markdown = (
        f"## {name}\n\n"
        f"### Original Content\n{content_text}\n\n"
        f"### Formatting Blueprint\n{format_text}"
    )

    sections.append({
        "index": index,
        "name": name,
        "fn_name": fn_name,
        "is_header": is_header,
        "is_footer": is_footer,
        "markdown": markdown,
    })
