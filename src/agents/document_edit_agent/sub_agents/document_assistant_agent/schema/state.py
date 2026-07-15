from typing import Literal, TypedDict, Any, Annotated
from langgraph.graph.message import add_messages

class DocumentAssistantState(TypedDict):
    user_message: str
    final_answer: str
    status: Literal['running', 'complete', 'failed']
    document_id: str
    messages: Annotated[list[Any], add_messages]
