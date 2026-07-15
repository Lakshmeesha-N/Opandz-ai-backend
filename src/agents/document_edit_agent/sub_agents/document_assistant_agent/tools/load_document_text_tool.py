# src/agents/document_assistant_agent/tools/load_document_text_tool.py

import json
import subprocess
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from src.agents.document_edit_agent.helpers.load_document import (
    _load_generated_document,
)


@tool
def load_document_text_tool(document_id: str):
    """
    Loads a generated document, writes the DocxJS code to a temporary
    JavaScript file, runs the Node.js extractor, and returns the extracted
    section-wise text.
    """

    document = _load_generated_document(document_id)

    docxjs_code = document["generated_docxjs_code"]

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".js",
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_file.write(docxjs_code)
        temp_js_path = temp_file.name

    extractor_script = (
        Path(__file__).resolve().parent.parent
        / "scripts"
        / "extract_text.js"
    )

    result = subprocess.run(
        [
            "node",
            str(extractor_script),
            temp_js_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)