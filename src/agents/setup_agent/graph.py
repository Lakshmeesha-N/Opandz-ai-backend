# src/agents/setup_agent/graph.py

from langgraph.graph import StateGraph, START, END

from src.agents.setup_agent.schema.global_state import AgentState

from src.agents.setup_agent.nodes.load_document import (
    load_document,
)

from src.agents.setup_agent.nodes.extract_docx_blueprint import (
    extract_docx_blueprint,
)

from src.agents.setup_agent.nodes.generate_docx_config import (
    generate_docx_config,
)

from src.agents.setup_agent.nodes.generate_field_manifest import (
    generate_field_manifest_node,
)


# -----------------------------
# Router
# -----------------------------

def route_document(state: AgentState) -> str:
    """
    Route execution based on document type.
    """
    if state.get("error"):
        return "error"

    if state.get("file_type") == "docx":
        return "docx"

    elif state.get("file_type") == "pdf":
        return "pdf"

    raise ValueError(
        f"Unsupported file type: {state.get('file_type')}"
    )


# -----------------------------
# Build Graph
# -----------------------------

graph = StateGraph(AgentState)


# Nodes
graph.add_node(
    "load_document",
    load_document,
)

graph.add_node(
    "extract_docx_blueprint",
    extract_docx_blueprint,
)

graph.add_node(
    "generate_docx_config",
    generate_docx_config,
)

graph.add_node(
    "generate_field_manifest",
    generate_field_manifest_node,
)


# Start
graph.add_edge(
    START,
    "load_document",
)


# Route after loading
graph.add_conditional_edges(
    "load_document",
    route_document,
    {
        "docx": "extract_docx_blueprint",
        "error": END,
        # "pdf": "extract_pdf_blueprint"  # add later
    },
)


# DOCX extraction
graph.add_edge(
    "extract_docx_blueprint",
    "generate_docx_config",
)

graph.add_edge(
    "extract_docx_blueprint",
    "generate_field_manifest",
)


# Parallel nodes finish
graph.add_edge(
    "generate_docx_config",
    END,
)

graph.add_edge(
    "generate_field_manifest",
    END,
)

# Compile graph
setup_agent_graph = graph.compile()

if __name__ == "__main__":

    try:

        png_data = setup_agent_graph.get_graph().draw_mermaid_png()

        with open(
            "setup_agent_graph.png",
            "wb",
        ) as f:
            f.write(png_data)

        print(
            "Graph image saved: setup_agent_graph.png"
        )

    except Exception as e:

        print(
            f"Failed to generate graph image: {e}"
        )
