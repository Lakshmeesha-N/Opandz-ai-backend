from src.agents.setup_agent.schema.docx_schema import  DocumentBlueprint
from typing import TypedDict, List, Optional, Literal

class AgentState(TypedDict):
    file_path: str
    file_type: str  # "docx" or "pdf"
    docx_blueprint: Optional[DocumentBlueprint]
    pdf_blueprint: Optional[List[DocumentBlueprint]]
    lawyer_id: str
    template_id: str
    temp_dir: Optional[str]  # path to temp directory for unzipped docx files
    error: Optional[str]