# src/agents/document_edit_agent/tool_node.py

from langgraph.prebuilt import ToolNode

from src.agents.document_edit_agent.tools.get_available_functions import (
    get_available_functions,
)

from src.agents.document_edit_agent.tools.get_function_code import (
    get_function_code,
)

from src.agents.document_edit_agent.tools.replace_function_code import (
    replace_function_code,
)

from src.agents.document_edit_agent.tools.validate_docxjs import (
    validate_docxjs,
)


tool_node = ToolNode(
    [
        get_available_functions,
        get_function_code,
        replace_function_code,
        validate_docxjs,
    ],
)