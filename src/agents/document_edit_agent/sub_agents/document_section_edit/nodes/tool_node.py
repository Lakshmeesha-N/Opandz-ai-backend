# src/agents/document_edit_agent/tool_node.py

from langgraph.prebuilt import ToolNode

from src.agents.document_edit_agent.sub_agents.document_section_edit.tools.get_available_functions import (
    get_available_functions,
)

from src.agents.document_edit_agent.sub_agents.document_section_edit.tools.get_function_code import (
    get_function_code,
)

from src.agents.document_edit_agent.sub_agents.document_section_edit.tools.get_all_document_text import (
    get_all_document_text,
)

from src.agents.document_edit_agent.sub_agents.document_section_edit.tools.replace_multiple_functions_code import (
    replace_multiple_functions_code,
)

from src.agents.document_edit_agent.sub_agents.document_section_edit.tools.validate_docxjs import (
    validate_docxjs,
)


tool_node = ToolNode(
    [
        get_available_functions,
        get_function_code,
        get_all_document_text,
        replace_multiple_functions_code,
        validate_docxjs,
    ],
)