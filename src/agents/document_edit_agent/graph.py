# src/agents/document_edit_agent/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode

from src.agents.document_edit_agent.schema.state import DocumentEditState
from src.agents.document_edit_agent.nodes.router_node import router_node

# Import Assistant sub-agent nodes & tools
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.nodes.assistant_node import (
    assistant_node,
)
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.tools.load_document_text_tool import (
    load_document_text_tool,
)

# Import Section Edit sub-agent nodes & tools
from src.agents.document_edit_agent.sub_agents.document_section_edit.nodes.load_document_node import (
    load_document_node,
)
from src.agents.document_edit_agent.sub_agents.document_section_edit.nodes.document_section_edit_node import (
    document_section_edit_node,
)
from src.agents.document_edit_agent.sub_agents.document_section_edit.nodes.tool_node import (
    tool_node as edit_tool_node,
)


# ---------------------------------------------------------------------
# Route function — reads the router's decision from state
# ---------------------------------------------------------------------

def route_after_router(state: DocumentEditState) -> str:
    """Route to the correct sub-agent based on the router's decision."""
    if state.get("error"):
        return "end"
    next_agent = state.get("next_agent", "assistant")
    if next_agent == "editor":
        return "editor"
    return "assistant"


def route_after_load_edit(state: DocumentEditState) -> str:
    """Route to edit node or end if error occurs during loading."""
    if state.get("error"):
        return "end"
    return "document_edit_agent"


# ---------------------------------------------------------------------
# Build Graph (Fully Expanded Workflow)
# ---------------------------------------------------------------------

builder = StateGraph(DocumentEditState)

# Parent Router Node
builder.add_node("router", router_node)

# Assistant workflow nodes
builder.add_node("assistant", assistant_node)
builder.add_node("assistant_tools", ToolNode([load_document_text_tool]))

# Editor workflow nodes
builder.add_node("load_document", load_document_node)
builder.add_node("document_edit_agent", document_section_edit_node)
builder.add_node("edit_tools", edit_tool_node)


# Start
builder.add_edge(START, "router")


# Router branching
builder.add_conditional_edges(
    "router",
    route_after_router,
    {
        "assistant": "assistant",
        "editor": "load_document",
        "end": END,
    },
)


# ── 1. Assistant Workflow ──
builder.add_conditional_edges(
    "assistant",
    tools_condition,
    {
        "tools": "assistant_tools",
        "__end__": END,
    },
)
builder.add_edge("assistant_tools", "assistant")


# ── 2. Editor Workflow ──
builder.add_conditional_edges(
    "load_document",
    route_after_load_edit,
    {
        "document_edit_agent": "document_edit_agent",
        "end": END,
    },
)

builder.add_conditional_edges(
    "document_edit_agent",
    tools_condition,
    {
        "tools": "edit_tools",
        "__end__": END,
    },
)
builder.add_edge("edit_tools", "document_edit_agent")


# Compile the unified graph
document_edit_graph = builder.compile()
graph = document_edit_graph



if __name__ == "__main__":
    try:
        # Generate the fully expanded flow image
        png_data = document_edit_graph.get_graph().draw_mermaid_png()
        with open("document_edit_full.png", "wb") as f:
            f.write(png_data)
        print("Graph image saved: document_edit_full.png")
    except Exception as e:
        print(f"Failed to generate graph image: {e}")
