# src/agents/document_generation_agent/graph.py

from langgraph.graph import (
    StateGraph,
    END,
)

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.nodes.load_intake_session import (
    load_generation_context,
)

from src.agents.document_generation_agent.nodes.generate_docxjs_code import (
    generate_docxjs_code,
)

from src.agents.document_generation_agent.nodes.validate_generated_docxjs_code import (
    validate_generated_docxjs_code,
)

from src.agents.document_generation_agent.nodes.fix_docxjs_code import (
    fix_docxjs_code,
)

from src.agents.document_generation_agent.nodes.store_generated_docxjs_code import (
    store_generated_docxjs_code_node,
)


def route_after_validation(
    state: AgentState,
) -> str:

    if state.get(
        "error",
    ):
        return "fix"

    return "store"


graph = StateGraph(
    AgentState,
)

graph.add_node(
    "load_generation_context",
    load_generation_context,
)

graph.add_node(
    "generate_docxjs_code",
    generate_docxjs_code,
)

graph.add_node(
    "validate_generated_docxjs_code",
    validate_generated_docxjs_code,
)

graph.add_node(
    "fix_docxjs_code",
    fix_docxjs_code,
)

graph.add_node(
    "store_generated_docxjs_code",
    store_generated_docxjs_code_node,
)

graph.set_entry_point(
    "load_generation_context",
)

graph.add_edge(
    "load_generation_context",
    "generate_docxjs_code",
)

graph.add_edge(
    "generate_docxjs_code",
    "validate_generated_docxjs_code",
)

graph.add_conditional_edges(
    "validate_generated_docxjs_code",
    route_after_validation,
    {
        "fix": "fix_docxjs_code",
        "store": "store_generated_docxjs_code",
    },
)

graph.add_edge(
    "fix_docxjs_code",
    "validate_generated_docxjs_code",
)

graph.add_edge(
    "store_generated_docxjs_code",
    END,
)

document_generation_graph = graph.compile()


if __name__ == "__main__":

    try:

        png_data = document_generation_graph.get_graph().draw_mermaid_png()

        with open(
            "docs_generation.png",
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