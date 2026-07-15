# src/agents/document_edit_agent/schema/global_state.py
from typing import TypedDict, Optional, Any, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):

    lawyer_id: str
    template_id: Optional[str]
    document_id: str

    user_message: str

    temp_file_path: str

    document_config: dict[str, Any]
    blueprint: dict[str, Any]
    messages: Annotated[list[Any], add_messages]
    uploaded_files: Optional[list[str]]
    error: Optional[str]