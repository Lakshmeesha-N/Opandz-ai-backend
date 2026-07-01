# src/agents/case_intake_agent/nodes/calculate_completion.py

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)


def calculate_completion(
    state: AgentState,
) -> AgentState:
    """
    Calculate:
    - completion percentage
    - missing fields
    - ready_to_generate
    """

    try:

        field_manifest = state.get(
            "field_manifest",
            {},
        )

        case_data = state.get(
            "case_data",
            {},
        )

        fields = field_manifest.get(
            "required_fields",
            field_manifest.get("fields", []),
        )

        total_fields = len(fields)

        if total_fields == 0:
            return {
                **state,
                "completion_percentage": 100.0,
                "missing_fields": [],
                "ready_to_generate": True,
                "error": None,
            }

        filled_count = 0
        missing_fields = []

        for field in fields:

            field_name = field.get("name")

            value = case_data.get(
                field_name
            )

            if (
                value is not None
                and value != ""
            ):
                filled_count += 1

            else:
                missing_fields.append(
                    field_name
                )

        completion_percentage = (
            filled_count / total_fields
        ) * 100

        ready_to_generate = (
            completion_percentage >= 90
        )

        return {
            **state,
            "completion_percentage": round(
                completion_percentage,
                2,
            ),
            "missing_fields": missing_fields,
            "ready_to_generate": ready_to_generate,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }