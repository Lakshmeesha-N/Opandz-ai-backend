# src/agents/case_intake_agent/nodes/save_session_state.py

import asyncio

from firebase_admin import firestore

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.utils.session_storage import (
    save_intake_session,
)


async def save_session_state(
    state: AgentState,
) -> AgentState:
    """
    Persist session state without blocking
    the event loop.
    """

    try:

        session_id = state["session_id"]

        document_data = {
            "session_id": session_id,
            "template_id": state.get(
                "template_id"
            ),
            "field_manifest": state.get(
                "field_manifest",
                {},
            ),
            "case_data": state.get(
                "case_data",
                {},
            ),
            "completion_percentage": state.get(
                "completion_percentage",
                0.0,
            ),
            "ready_to_generate": state.get(
                "ready_to_generate",
                False,
            ),
            "next_question": state.get(
                "next_question",
            ),
            "missing_fields": state.get(
                "missing_fields",
                [],
            ),
            "error": state.get(
                "error",
            ),
        }


        await asyncio.to_thread(
            save_intake_session,
            session_id,
            document_data,
        )

        return state


    except Exception as e:

        return {
            **state,
            "error": str(e),
        }