import json


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
                section_entry["blocks"].append({
                    "block_id": block["block_id"],
                    "block_type": block["block_type"],
                    "style_name": (block.get("paragraph_style") or {}).get("style_name"),
                    "content": block.get("table_data") if is_table else block.get("content") or ""
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