# src/agents/case_intake_agent/nodes/load_field_manifest.py

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.utils.fetch_manifest import (
    get_field_manifest,
)


async def load_field_manifest(
    state: AgentState,
) -> AgentState:
    """
    Load field manifest and initialize case_data.
    """

    try:
        field_manifest = await get_field_manifest(
            state["template_id"]
        )

        import asyncio
        from src.agents.case_intake_agent.utils.session_storage import get_intake_session

        # Fetch existing session state from Firestore
        session_id = state.get("session_id", "")
        existing_session = await asyncio.to_thread(get_intake_session, session_id)
        existing_case_data = existing_session.get("case_data", {})

        case_data = {}

        fields = (
            field_manifest.get("fields")
            or field_manifest.get("field_manifest", {}).get("fields")
            or field_manifest.get("required_fields", [])
        )

        for field in fields:
            field_name = field.get("field_name") or field.get("field") or field.get("name")

            if field_name:
                # Retain existing answers, defaulting to None only if empty
                case_data[field_name] = existing_case_data.get(field_name, None)

        # Preserve the accumulated important_information list across turns
        case_data["important_information"] = existing_case_data.get(
            "important_information", []
        )

        return {
            **state,
            "field_manifest": field_manifest,
            "case_data": case_data,
            "completion_percentage": 0.0,
            "ready_to_generate": False,
            "error": None,
        }


    except Exception as e:
        return {
            **state,
            "error": str(e),
        }