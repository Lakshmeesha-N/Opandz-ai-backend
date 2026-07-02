# src/agents/document_generation_agent/helpers/validate_docxjs_code.py

import re
import tempfile
import subprocess
from pathlib import Path


def validate_docxjs_code(
    generated_code: str,
) -> tuple[bool, str | None]:

    try:

        if not generated_code.strip():

            return (
                False,
                "Empty code returned",
            )

        if not re.search(
            r"export\s+function\s+buildDocument\s*\(",
            generated_code,
        ):
            return (
                False,
                "buildDocument function not found",
            )

        with tempfile.NamedTemporaryFile(
            suffix=".js",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as temp_file:

            temp_file.write(
                generated_code,
            )

            temp_path = Path(
                temp_file.name,
            )

        result = subprocess.run(
            [
                "node",
                "--check",
                str(temp_path),
            ],
            capture_output=True,
            text=True,
        )

        temp_path.unlink(
            missing_ok=True,
        )

        if result.returncode != 0:

            return (
                False,
                result.stderr,
            )

        return (
            True,
            None,
        )

    except FileNotFoundError:
        # Node.js is not installed in the current environment; log warning and skip
        import logging
        logging.getLogger(__name__).warning("Node.js is not installed. Skipping syntax check.")
        return (
            True,
            None,
        )
    except Exception as e:

        return (
            False,
            str(e),
        )