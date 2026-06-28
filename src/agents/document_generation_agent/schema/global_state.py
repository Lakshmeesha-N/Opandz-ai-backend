from typing import TypedDict, Optional, Any


class AgentState(TypedDict):

    session_id: str
    template_id: str

    document_blueprint_source: str

    case_data: dict[str, Any]

    document_config: dict[str, Any]
    blueprint: dict[str, Any]

    output_docx_path: Optional[str]
    output_pdf_path: Optional[str]
    generated_docxjs_code: str

    error: Optional[str]