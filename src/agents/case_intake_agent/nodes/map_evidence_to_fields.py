# src/agents/case_intake_agent/nodes/map_evidence_to_fields.py

import json

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.prompts.field_mapping_prompt import (
    create_field_mapping_prompt,
)

from src.llm.llm import get_llm


async def map_evidence_to_fields(
    state: AgentState,
) -> AgentState:
    """
    Maps extracted evidence and user messages
    to the field manifest and updates case_data.
    """

    if state.get("error"):
        return state

    try:

        field_manifest = state["field_manifest"]

        evidence = state.get(
            "extracted_evidence",
            [],
        )

        user_message = state.get(
            "user_message",
            "",
        )

        current_case_data = state.get(
            "case_data",
            {},
        )

        prompt = create_field_mapping_prompt(
            field_manifest=field_manifest,
            evidence=evidence,
            user_message=user_message,
        )

        llm = get_llm()

        response = await llm.ainvoke(
            prompt
        )

        content = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )

        extracted_fields = json.loads(
            content
        )

        # Only update fields that
        # already exist in case_data

        for key, value in extracted_fields.items():

            if (
                key in current_case_data
                and value is not None
                and value != ""
            ):
                current_case_data[key] = value

        return {
            **state,
            "case_data": current_case_data,
        }


    except Exception as e:

        return {
            **state,
            "error": str(e),
        }

