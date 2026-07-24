# src/agents/document_generation_agent/prompts/create_assembly_prompt.py


def create_assembly_prompt(
    function_names: list[str],
    header_fn: str | None,
    footer_fn: str | None,
    metadata_md: str,
) -> str:
    """
    Build a prompt to generate ONLY the buildDocument() function
    that assembles all the already-generated section functions.
    """
    body_fns = [
        fn for fn in function_names
        if fn not in (header_fn, footer_fn)
    ]

    header_ref = f"build_section_header()" if header_fn else "null"
    footer_ref = f"build_section_footer()" if footer_fn else "null"

    body_spread = "\n          ".join([f"...{fn}()," for fn in body_fns])

    return f"""You are a DOCX.js code generator. Generate ONLY the buildDocument() function.

==================================================================
ALREADY GENERATED FUNCTIONS (do NOT redefine them)
==================================================================

{chr(10).join(f"  - {fn}" for fn in function_names)}

==================================================================
PAGE SETUP (from blueprint)
==================================================================

{metadata_md[:3000]}

==================================================================
RULES
==================================================================

1. Output ONLY the buildDocument() export function — no imports, no section functions.
2. Use the page dimensions (width, height) and margins EXACTLY as stated in PAGE SETUP.
   Write Twip values as plain numbers — do NOT wrap in convertInchesToTwip().
3. Assign headers: {{ default: {header_ref} }} when a header function exists.
4. Assign footers: {{ default: {footer_ref} }} when a footer function exists.
5. Place all body content functions in children: [...] using spread operator.
6. If the blueprint defines multiple DOCX sections (different page margins/sizes),
   create multiple section objects inside sections: [].
7. The returned Document must be directly executable with Packer.toBuffer().
8. buildDocument() takes ZERO parameters.

==================================================================
EXPECTED SHAPE
==================================================================

export function buildDocument() {{
  return new Document({{
    sections: [
      {{
        properties: {{
          page: {{
            size: {{ width: <twips>, height: <twips> }},
            margin: {{ top: <twips>, bottom: <twips>, left: <twips>, right: <twips> }},
          }},
        }},
        headers: {{ default: {header_ref} }},
        footers: {{ default: {footer_ref} }},
        children: [
          {body_spread}
        ],
      }},
    ],
  }});
}}

==================================================================
OUTPUT
==================================================================

Output ONLY the complete buildDocument() function. Start with:
export function buildDocument() {{
"""
