# src/agents/document_edit_agent/helpers/build_llm_document_context.py

def build_llm_document_context(
    document_config: dict,
) -> dict:

    sections = []

    for section in document_config.get(
        "sections",
        [],
    ):

        sections.append(
            {
                "header": section.get(
                    "header_group",
                    {},
                ).get(
                    "name",
                ),
                "footer": section.get(
                    "footer_group",
                    {},
                ).get(
                    "name",
                ),
                "semantic_groups": [
                    {
                        "name": group.get(
                            "name",
                        ),
                        "description": group.get(
                            "description",
                        ),
                    }
                    for group in section.get(
                        "semantic_groups",
                        [],
                    )
                ],
            }
        )

    return {
        "sections": sections,
    }