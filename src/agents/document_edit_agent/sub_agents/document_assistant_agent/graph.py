# src/agents/document_edit_agent/sub_agents/document_assistant_agent/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode

from src.agents.document_edit_agent.sub_agents.document_assistant_agent.schema.state import DocumentAssistantState
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.nodes.assistant_node import assistant_node
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.tools.load_document_text_tool import load_document_text_tool

# Build graph builder
builder = StateGraph(DocumentAssistantState)

# Define nodes
builder.add_node("assistant", assistant_node)
builder.add_node("tools", ToolNode([load_document_text_tool]))

# Define edges
builder.add_edge(START, "assistant")

builder.add_conditional_edges(
    "assistant",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    }
)

builder.add_edge("tools", "assistant")

# Compile graph
document_assistant_graph = builder.compile()

if __name__ == "__main__":

    try:

        png_data = document_assistant_graph.get_graph().draw_mermaid_png()

        with open(
            "document_assistant.png",
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