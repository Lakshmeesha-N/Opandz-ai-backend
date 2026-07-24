# src/agents/document_generation_agent/nodes/generate_docxjs_code.py

import logging
import asyncio

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)
from src.agents.document_generation_agent.helpers.blueprint_parser import (
    parse_blueprint_sections,
)
from src.agents.document_generation_agent.prompts.create_section_docxjs_prompt import (
    create_section_docxjs_prompt,
)
from src.agents.document_generation_agent.prompts.create_assembly_prompt import (
    create_assembly_prompt,
)
from src.agents.document_generation_agent.prompts.create_docxjs_generation_prompt import (
    create_docxjs_generation_prompt,
)
from src.llm.llm import (
    get_llm,
)

logger = logging.getLogger(__name__)

def _build_dynamic_docx_imports(body_code: str) -> str:
    """
    Dynamically scans generated section code for all referenced docx constructors,
    enums, types, and helper functions, and generates a complete, clean import statement.
    Guarantees no missing import reference errors regardless of what APIs the LLM uses.
    """
    import re

    # Baseline core imports every document needs
    imports = {
        "Document", "Packer", "Paragraph", "TextRun", "Header", "Footer",
        "Table", "TableRow", "TableCell", "WidthType", "AlignmentType"
    }

    # 1. Any constructor call: new X(...)
    constructors = re.findall(r'\bnew\s+([A-Z][a-zA-Z0-9_]+)\b', body_code)
    imports.update(constructors)

    # 2. Any enum or class constant: X.Y (e.g., LineRule.MULTIPLE, BorderStyle.SINGLE)
    enums = re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\.[A-Z0-9_]+\b', body_code)
    imports.update(enums)

    # 3. Common helper functions (e.g., convertInchesToTwip)
    helpers = re.findall(r'\b(convert[A-Za-z0-9_]+)\b', body_code)
    imports.update(helpers)

    # Clean up any non-docx identifiers if any slip through
    imports.discard("Array")
    imports.discard("String")
    imports.discard("Object")
    imports.discard("Number")
    imports.discard("Boolean")
    imports.discard("Date")
    imports.discard("Math")
    imports.discard("JSON")
    imports.discard("RegExp")
    imports.discard("Promise")
    imports.discard("Error")
    imports.discard("CASE_DATA")

    sorted_imports = ",\n  ".join(sorted(imports))
    return f"import {{\n  {sorted_imports},\n}} from \"docx\";"


def _extract_text(response) -> str:
    """Safely extract string content from an LLM response object."""
    content = getattr(response, "content", str(response))
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text", ""))
        return "".join(parts)
    return str(content)


def _clean_fn_output(raw: str, fn_name: str) -> str:
    """
    Ensure the LLM output is a self-contained export function.
    The prompt asks the model to start with 'export function {fn_name}() {'
    but sometimes the model includes a markdown code fence or repeats the
    opening brace. Normalize to a clean function string.
    """
    import re

    # Strip markdown code fences
    raw = re.sub(r"^```(?:javascript|js)?\s*\n?", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"\n?```$", "", raw.strip())
    raw = raw.strip()

    # If the model started with the function signature already, use as-is
    if raw.startswith("export function"):
        return raw

    # If model output starts with the body (without the signature),
    # prepend the signature
    return f"export function {fn_name}() {{\n{raw}\n}}"


async def _generate_section_fn(
    llm,
    section: dict,
    case_data: dict,
    metadata_md: str,
) -> str:
    """Generate one DOCX.js export function for a single blueprint section."""
    prompt = create_section_docxjs_prompt(
        fn_name=section["fn_name"],
        section_markdown=section["markdown"],
        case_data=case_data,
        metadata_md=metadata_md,
        is_header=section["is_header"],
        is_footer=section["is_footer"],
    )
    response = await llm.ainvoke(prompt)
    raw = _extract_text(response)
    fn_code = _clean_fn_output(raw, section["fn_name"])
    fn_code = _fix_api_names(fn_code)
    logger.info(
        "[generate_docxjs_code] section '%s' → fn '%s' (%d chars)",
        section["name"],
        section["fn_name"],
        len(fn_code),
    )
    return fn_code


def _fix_api_names(code: str) -> str:
    """Post-process generated code to fix common DOCX.js API name mistakes."""
    import re
    # Alignment.X → AlignmentType.X  (Alignment is not exported from docx)
    code = re.sub(r'\bAlignment\.(?!Type)', 'AlignmentType.', code)
    # WidthType.TWIPS → WidthType.DXA
    code = code.replace('WidthType.TWIPS', 'WidthType.DXA')
    # Remove inline const CASE_DATA = {...} blocks that bloat the output
    code = re.sub(
        r'\n\s*const CASE_DATA\s*=\s*\{[^}]*(?:\{[^}]*\}[^}]*)?\};\s*\n',
        '\n',
        code,
        flags=re.DOTALL,
    )
    return code


async def generate_docxjs_code(
    state: AgentState,
) -> AgentState:

    try:
        logger.info("[generate_docxjs_code] START")

        blueprint_markdown: str = state.get("blueprint", "")
        case_data: dict = state.get("case_data", {})

        # ── 1. Parse blueprint into sections ──────────────────────────────
        parsed = parse_blueprint_sections(blueprint_markdown)
        metadata_md: str = parsed["metadata"]
        sections: list = parsed["sections"]

        # ── 2. Fall back to old single-call approach if no sections found ──
        if not sections:
            logger.warning(
                "[generate_docxjs_code] No sections parsed from blueprint — "
                "falling back to single-call generation"
            )
            prompt = create_docxjs_generation_prompt(state)
            llm = get_llm()
            response = await llm.ainvoke(prompt)
            generated_code = _extract_text(response)
            logger.info(
                "[generate_docxjs_code] FALLBACK SUCCESS: %d chars",
                len(generated_code),
            )
            return {
                **state,
                "generated_docxjs_code": generated_code,
                "error": None,
            }

        # ── 3. Deduplicate sections by fn_name (parser may return dupes) ──
        seen_fn_names: set[str] = set()
        unique_sections: list = []
        for sec in sections:
            if sec["fn_name"] not in seen_fn_names:
                seen_fn_names.add(sec["fn_name"])
                unique_sections.append(sec)
        sections = unique_sections

        # ── 4. Generate one function per section (sequential) ─────────────
        llm = get_llm()
        section_functions: list[str] = []
        function_names: list[str] = []
        header_fn: str | None = None
        footer_fn: str | None = None

        logger.info(
            "[generate_docxjs_code] Generating %d section functions...",
            len(sections),
        )

        for section in sections:
            fn_code = await _generate_section_fn(llm, section, case_data, metadata_md)
            section_functions.append(fn_code)
            function_names.append(section["fn_name"])
            if section["is_header"]:
                header_fn = section["fn_name"]
            if section["is_footer"]:
                footer_fn = section["fn_name"]

        # ── 5. Build buildDocument() deterministically in Python (Zero LLM Call) ─
        logger.info("[generate_docxjs_code] Assembling buildDocument() in Python...")

        body_fns = [fn for fn in function_names if fn not in (header_fn, footer_fn)]
        body_spreads = ",\n          ".join(f"...{fn}()" for fn in body_fns)

        # Only include header/footer props if we actually have those functions;
        # NEVER pass null — DOCX.js treats null header/footer as a new Section Break.
        header_prop = f"headers: {{ default: {header_fn}() }}," if header_fn else ""
        footer_prop = f"footers: {{ default: {footer_fn}() }}," if footer_fn else ""

        build_doc_fn = f"""export function buildDocument() {{
  return new Document({{
    sections: [
      {{
        properties: {{
          page: {{
            size: {{ width: 12240, height: 20160 }},
            margin: {{ top: 362, bottom: 1210, left: 1440, right: 1440 }},
          }},
        }},
        {header_prop}
        {footer_prop}
        children: [
          {body_spreads}
        ],
      }},
    ],
  }});
}}"""

        # ── 5. Assemble final file with dynamically generated imports ──────
        body_code = "\n\n".join(section_functions) + "\n\n" + build_doc_fn
        dynamic_imports = _build_dynamic_docx_imports(body_code)

        final_code = (
            dynamic_imports
            + "\n\n"
            + body_code
        )

        logger.info(
            "[generate_docxjs_code] SUCCESS: %d sections → %d total chars",
            len(sections),
            len(final_code),
        )

        return {
            **state,
            "generated_docxjs_code": final_code,
            "error": None,
        }

    except Exception as e:
        logger.exception("[generate_docxjs_code] ERROR: %s", str(e))
        return {
            **state,
            "error": str(e),
        }