# src/agents/case_intake_agent/graph.py

import logging
from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.nodes.load_field_manifest import (
    load_field_manifest,
)

from src.agents.case_intake_agent.nodes.extract_evidence import (
    extract_evidence,
)

from src.agents.case_intake_agent.nodes.map_evidence_to_fields import (
    map_evidence_to_fields,
)

from src.agents.case_intake_agent.nodes.calculate_completion import (
    calculate_completion,
)

from src.agents.case_intake_agent.nodes.determine_next_action import (
    determine_next_action,
)

from src.agents.case_intake_agent.nodes.generate_followup_question import (
    generate_followup_question,
)

from src.agents.case_intake_agent.nodes.save_session_state import (
    save_session_state,
)

logger = logging.getLogger(__name__)


def has_uploaded_files(
    state: AgentState,
) -> str:

    uploaded_files = state.get(
        "uploaded_files",
        [],
    )

    if uploaded_files:
        logger.info("[has_uploaded_files] Routing to extract_evidence (found files)")
        return "extract_evidence"

    logger.info("[has_uploaded_files] Routing to map_evidence_to_fields (no files)")
    return "map_evidence_to_fields"


def route_next_action(
    state: AgentState,
) -> str:

    next_action = state.get(
        "next_action",
        "ask_question",
    )
    logger.info("[route_next_action] Routing to next action: %s", next_action)
    return next_action


graph_builder = StateGraph(
    AgentState
)

# Nodes

graph_builder.add_node(
    "load_field_manifest",
    load_field_manifest,
)

graph_builder.add_node(
    "extract_evidence",
    extract_evidence,
)

graph_builder.add_node(
    "map_evidence_to_fields",
    map_evidence_to_fields,
)

graph_builder.add_node(
    "calculate_completion",
    calculate_completion,
)

graph_builder.add_node(
    "determine_next_action",
    determine_next_action,
)

graph_builder.add_node(
    "generate_followup_question",
    generate_followup_question,
)

graph_builder.add_node(
    "save_session_state",
    save_session_state,
)

# Flow

graph_builder.add_edge(
    START,
    "load_field_manifest",
)

graph_builder.add_conditional_edges(
    "load_field_manifest",
    has_uploaded_files,
    {
        "extract_evidence": "extract_evidence",
        "map_evidence_to_fields": "map_evidence_to_fields",
    },
)

graph_builder.add_edge(
    "extract_evidence",
    "map_evidence_to_fields",
)

graph_builder.add_edge(
    "map_evidence_to_fields",
    "calculate_completion",
)

graph_builder.add_edge(
    "calculate_completion",
    "determine_next_action",
)

graph_builder.add_conditional_edges(
    "determine_next_action",
    route_next_action,
    {
        "ask_question": "generate_followup_question",
        "ready_to_generate": "save_session_state",
    },
)

graph_builder.add_edge(
    "generate_followup_question",
    "save_session_state",
)

graph_builder.add_edge(
    "save_session_state",
    END,
)

graph = graph_builder.compile()

if __name__ == "__main__":

    try:

        png_data = graph.get_graph().draw_mermaid_png()

        with open(
            "case_intake_agent.png",
            "wb",
        ) as f:
            f.write(png_data)

        print(
            "Graph image saved: case_intake_agent.png"
        )

    except Exception as e:

        print(
            f"Failed to generate graph image: {e}"
        )