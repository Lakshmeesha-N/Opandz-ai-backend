# src/agents/document_edit_agent/graph.py

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.prebuilt import (
    tools_condition,
)

from src.agents.document_edit_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_edit_agent.nodes.load_document_node import (
    load_document_node,
)

from src.agents.document_edit_agent.nodes.document_edit_agent_node import (
    document_edit_agent_node,
)

from src.agents.document_edit_agent.nodes.tool_node import (
    tool_node,
)


builder = StateGraph(
    AgentState,
)

builder.add_node(
    "load_document",
    load_document_node,
)

builder.add_node(
    "document_edit_agent",
    document_edit_agent_node,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_edge(
    START,
    "load_document",
)

builder.add_edge(
    "load_document",
    "document_edit_agent",
)

builder.add_conditional_edges(
    "document_edit_agent",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    },
)

builder.add_edge(
    "tools",
    "document_edit_agent",
)

graph = builder.compile()


if __name__ == "__main__":

    try:

        png_data = graph.get_graph().draw_mermaid_png()

        with open(
            "document_edit.png",
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