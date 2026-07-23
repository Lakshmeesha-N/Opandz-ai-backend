# src/agents/setup_agent/graph.py

from langgraph.graph import StateGraph, START, END

from src.agents.setup_agent.schema.global_state import AgentState

from src.agents.setup_agent.nodes.load_document import (
    load_document,
)

from src.agents.setup_agent.nodes.convert_pdf import (
    convert_pdf_node,
)

from src.agents.setup_agent.nodes.extract_docx_blueprint import (
    extract_docx_blueprint,
)

from src.agents.setup_agent.nodes.unzip_docx import (
    unzip_docx,
)

from src.agents.setup_agent.nodes.create_blueprint_metadata import (
    create_blueprint_metadata,
)

from src.agents.setup_agent.nodes.generate_full_blueprint_body import (
    generate_full_blueprint_body,
)

from src.agents.setup_agent.nodes.generate_field_manifest import (
    generate_field_manifest_node,
)

from src.agents.setup_agent.nodes.merge_and_upload import (
    merge_and_upload,
)

from src.agents.setup_agent.nodes.clean_temp import (
    clean_temp,
)


# -----------------------------
# Routers
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


def route_after_node(state: AgentState) -> str:
    """
    Generic router: if any error is set, jump to clean_temp;
    otherwise continue to the next node.
    """
    if state.get("error"):
        return "error"
    return "continue"


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
    "convert_pdf",
    convert_pdf_node,
)

graph.add_node(
    "extract_docx_blueprint",
    extract_docx_blueprint,
)

graph.add_node(
    "unzip_docx",
    unzip_docx,
)

graph.add_node(
    "create_blueprint_metadata",
    create_blueprint_metadata,
)

graph.add_node(
    "generate_full_blueprint_body",
    generate_full_blueprint_body,
)

graph.add_node(
    "generate_field_manifest",
    generate_field_manifest_node,
)

graph.add_node(
    "merge_and_upload",
    merge_and_upload,
)

graph.add_node(
    "clean_temp",
    clean_temp,
)


# ── Edges ──

# Start → load_document
graph.add_edge(
    START,
    "load_document",
)


# Route after loading (docx / pdf / error)
graph.add_conditional_edges(
    "load_document",
    route_document,
    {
        "docx": "extract_docx_blueprint",
        "pdf": "convert_pdf",
        "error": END,
    },
)

# After PDF conversion, proceed to DOCX extraction
graph.add_edge(
    "convert_pdf",
    "extract_docx_blueprint",
)

# extract_docx_blueprint → check error → generate_field_manifest or clean_temp
graph.add_conditional_edges(
    "extract_docx_blueprint",
    route_after_node,
    {
        "continue": "generate_field_manifest",
        "error": "clean_temp",
    },
)

# generate_field_manifest → check error → unzip_docx or clean_temp
graph.add_conditional_edges(
    "generate_field_manifest",
    route_after_node,
    {
        "continue": "unzip_docx",
        "error": "clean_temp",
    },
)

# unzip_docx → check error → create_blueprint_metadata or clean_temp
graph.add_conditional_edges(
    "unzip_docx",
    route_after_node,
    {
        "continue": "create_blueprint_metadata",
        "error": "clean_temp",
    },
)

# create_blueprint_metadata → check error → generate_full_blueprint_body or clean_temp
graph.add_conditional_edges(
    "create_blueprint_metadata",
    route_after_node,
    {
        "continue": "generate_full_blueprint_body",
        "error": "clean_temp",
    },
)

# generate_full_blueprint_body → check error → merge_and_upload or clean_temp
graph.add_conditional_edges(
    "generate_full_blueprint_body",
    route_after_node,
    {
        "continue": "merge_and_upload",
        "error": "clean_temp",
    },
)

# merge_and_upload → clean_temp (always clean up)
graph.add_edge(
    "merge_and_upload",
    "clean_temp",
)

# clean_temp → END
graph.add_edge(
    "clean_temp",
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
