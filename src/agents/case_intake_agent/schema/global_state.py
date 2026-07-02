from typing import TypedDict, Optional, Any


class AgentState(TypedDict):
    session_id:str
    template_id: str
    lawyer_id: Optional[str]
    field_manifest: dict
    missing_fields: list[str]
    case_data: dict[str, Any]
    extracted_evidence: list[dict]
    uploaded_files: list[str]
    completion_percentage: float
    ready_to_generate: bool
    user_message: Optional[str]
    chat_history: list[dict]
    error: Optional[str]
    next_question: Optional[str]