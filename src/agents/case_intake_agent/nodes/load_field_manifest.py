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

        case_data = {}

        fields = field_manifest.get(
            "fields",
            []
        )

        for field in fields:
            field_name = field.get("name")

            if field_name:
                case_data[field_name] = None

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