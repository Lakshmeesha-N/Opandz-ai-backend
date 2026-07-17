import json


def extract_plain_text(blueprint: dict) -> str:
    """
    Extract a flat plain-text string from the document blueprint.
    Concatenates only the text content of every block (header, body, footer).
    Used for field manifest generation — formatting data is not needed.
    """
    lines = []
    for section in blueprint.get("sections", []):
        for area in ("header_blocks", "body_blocks", "footer_blocks"):
            for block in section.get(area, []):
                if block.get("block_type") == "table":
                    # Flatten table cell text
                    table_data = block.get("table_data") or {}
                    for row in table_data.get("rows", []):
                        cell_texts = [c for c in row.get("cells", []) if c]
                        if cell_texts:
                            lines.append(" | ".join(cell_texts))
                else:
                    text = block.get("content", "").strip()
                    if text:
                        lines.append(text)
    return "\n".join(lines)


def parse_blueprint(blueprint: dict) -> dict:
    result = {"title": blueprint.get("title", ""), "sections": []}

    for section in blueprint.get("sections", []):
        section_entry = {
            "section_id": section["section_id"],
            "metadata": section.get("metadata", {}),
            "blocks": []
        }

        for area in ("header_blocks", "body_blocks", "footer_blocks"):
            for block in section.get(area, []):
                is_table = block.get("block_type") == "table"
                paragraph_style = block.get("paragraph_style") or {}
                block_entry = {
                    "block_id": block["block_id"],
                    "block_type": block["block_type"],
                    "area": area.replace("_blocks", ""),
                    "style_name": paragraph_style.get("style_name"),
                    "style_id": paragraph_style.get("style_id"),
                    "content": block.get("table_data") if is_table else block.get("content") or "",
                }

                if paragraph_style.get("numbering"):
                    block_entry["numbering"] = paragraph_style.get("numbering")
                if paragraph_style.get("tab_stops"):
                    block_entry["tab_stops"] = paragraph_style.get("tab_stops")
                if paragraph_style.get("borders"):
                    block_entry["paragraph_borders"] = paragraph_style.get("borders")
                if block.get("image_slots"):
                    block_entry["image_slots"] = block.get("image_slots")

                section_entry["blocks"].append({
                    **block_entry
                })

        result["sections"].append(section_entry)

    return result


def print_parsed(parsed: dict) -> None:
    print(f"\nTitle: {parsed['title']}\n")
    for section in parsed["sections"]:
        print(f"=== {section['section_id']} ===")
        print(f"Metadata: {section['metadata']}\n")
        for block in section["blocks"]:
            if block["block_type"] == "table":
                preview = f"table with {len(block['content']['rows'])} rows"
            else:
                preview = block["content"][:80] + "..." if len(block["content"]) > 80 else block["content"]
            print(f"  [{block['block_id']}] type={block['block_type']} | style={block['style_name']} | content={preview!r}")
        print()


if __name__ == "__main__":
    with open(r"C:\Users\laksh\Desktop\Opandz_legal_new\test\Test_file_blueprint_none_rm.json", "r") as f:
        blueprint = json.load(f)

    parsed = parse_blueprint(blueprint)
    json.dump(parsed, open(r"C:\Users\laksh\Desktop\Opandz_legal_new\test\Test_file_parsed.json", "w"), indent=2)
    print_parsed(parsed)
