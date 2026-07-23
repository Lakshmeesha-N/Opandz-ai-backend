from typing import TypedDict, Optional, Any, Annotated, Literal
from langgraph.graph.message import add_messages

class DocumentEditState(TypedDict):
    lawyer_id: str
    template_id: Optional[str]
    document_id: str
    user_message: str
    temp_file_path: Optional[str]
    blueprint: Optional[str]
    messages: Annotated[list[Any], add_messages]
    uploaded_files: Optional[list[str]]
    error: Optional[str]
    
    # Router state
    next_agent: Optional[Literal["assistant", "editor"]]
    
    # Sub-agent state keys for seamless subgraph integration
    final_answer: Optional[str]
    status: Optional[Literal['running', 'complete', 'failed']]
