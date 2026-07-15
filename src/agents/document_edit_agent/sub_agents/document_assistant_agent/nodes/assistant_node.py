# src/agents/document_edit_agent/sub_agents/document_assistant_agent/nodes/assistant_node.py

import logging
from langchain_core.messages import HumanMessage, convert_to_messages
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.schema.state import DocumentAssistantState
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.prompts.system_prompt import get_system_prompt
from src.agents.document_edit_agent.sub_agents.document_assistant_agent.tools.load_document_text_tool import load_document_text_tool
from src.llm.llm import get_llm

logger = logging.getLogger(__name__)

async def assistant_node(state: DocumentAssistantState) -> dict:
    try:
        logger.info("[assistant_node] START")
        
        messages = state.get("messages", [])
        if messages:
            messages = list(convert_to_messages(messages))
            # Filter empty messages
            messages = [m for m in messages if str(m.content).strip() or (hasattr(m, "tool_calls") and m.tool_calls)]
            
        user_message = state.get("user_message", "")
        if user_message and not any(isinstance(m, HumanMessage) and m.content == user_message for m in messages):
            messages.append(HumanMessage(content=user_message))
            
        document_id = state.get("document_id")
        if not messages or getattr(messages[0], "type", "") != "system":
            messages.insert(0, get_system_prompt(document_id))
            
        # Bind the document text loading tool to the LLM
        llm = get_llm().bind_tools([load_document_text_tool])
        
        response = await llm.ainvoke(messages)
        
        update = {
            "messages": [response],
            "status": "running"
        }
        
        # If no tool calls are requested, this response is the final answer
        if not (hasattr(response, "tool_calls") and response.tool_calls):
            update["final_answer"] = str(response.content)
            update["status"] = "complete"
            
        return update
        
    except Exception as e:
        logger.exception("[assistant_node] ERROR: %s", str(e))
        return {
            "status": "failed",
            "final_answer": f"Error running assistant: {str(e)}"
        }
