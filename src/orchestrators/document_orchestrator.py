# src/orchestrators/document_orchestrator.py

import logging

from src.agents.case_intake_agent.graph import (
    graph as case_intake_graph,
)

from src.agents.document_generation_agent.graph import (
    document_generation_graph,
)


class DocumentOrchestrator:

    async def run(
        self,
        initial_state: dict,
    ) -> dict:

        try:

            intake_result = (
                await case_intake_graph.ainvoke(
                    initial_state,
                )
            )

            if intake_result.get("error"):
                return intake_result

            if not intake_result.get(
                "ready_to_generate",
                False,
            ):
                return intake_result

            generation_state = (
                self._build_generation_state(
                    intake_result,
                )
            )

            generation_result = (
                await document_generation_graph.ainvoke(
                    generation_state,
                )
            )

            generation_result["ready_to_generate"] = True
            return generation_result

        except Exception as e:

            logging.exception(
                "Document orchestrator failed"
            )

            return {
                "error": str(e),
            }

    def _build_generation_state(
        self,
        intake_result: dict,
    ) -> dict:

        return {
            "session_id": intake_result[
                "session_id"
            ],
            "template_id": intake_result[
                "template_id"
            ],
            "lawyer_id": intake_result.get(
                "lawyer_id", ""
            ),
            "document_blueprint_source": "",
            "case_data": intake_result[
                "case_data"
            ],
            "document_config": {},
            "blueprint": {},
            "output_docx_path": None,
            "output_pdf_path": None,
            "generated_docxjs_code": "",
            "error": None,
        }


document_orchestrator = (
    DocumentOrchestrator()
)