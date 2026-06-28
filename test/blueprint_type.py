import json
from pathlib import Path

p = Path(r"C:\Users\laksh\Desktop\Opandz_legal_new\templates\111.json")
if not p.exists():
    print("File not found:", p)
    raise SystemExit(1)

with p.open("r", encoding="utf-8") as f:
    data = json.load(f)

print("Top-level type:", type(data))
if isinstance(data, dict):
    print("Keys:", list(data.keys()))

sections = data.get("sections")
print("'sections' type:", type(sections))
if isinstance(sections, list):
    print("sections length:", len(sections))
    if sections:
        print("first section type:", type(sections[0]))
        if isinstance(sections[0], dict):
            print("first section keys:", list(sections[0].keys()))

# Extra: show whether entire blueprint is wrapped in a list
# This helps determine if other code mistakenly wrapped the blueprint
print("Is top-level a list?", isinstance(data, list))
print("Is top-level['sections'] a list?", isinstance(sections, list))
