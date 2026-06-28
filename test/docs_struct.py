import sys
import os

# Ensure repository root is on sys.path so `src` is importable when running this file directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agents.setup_agent.graph import setup_agent_graph


initial_state = {
    'file_path': r'C:\Users\laksh\Desktop\Opandz_legal_new\test\Test_file.docx',
    'lawyer_id': 'lawyer_123',
    'template_id': '111',
}

setup_agent_graph.invoke(initial_state)