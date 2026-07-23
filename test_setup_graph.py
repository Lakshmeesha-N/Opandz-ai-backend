# test_setup_graph.py

import os
import sys

# Ensure project root is in path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force LOCAL_TEST and ALLOW_FIREBASE_MOCKS for local execution
os.environ["LOCAL_TEST"] = "True"
os.environ["ALLOW_FIREBASE_MOCKS"] = "True"

from src.agents.setup_agent.graph import setup_agent_graph
from src.utils.token_context import set_token_context, TokenTracker


def main():
    # Initial state mimicking test.py
    initial_state = {
        "file_path": os.path.join(project_root, "test", r"C:\Users\laksh\Downloads\1CG22AD009_ Report-1-20.pdf"),
        "file_type": "pdf",
        "lawyer_id": "test_lawyer",
        "template_id": "report test",
        "error": None,
    }

    # Set token-tracking context for user & agent
    set_token_context(initial_state["lawyer_id"], "setup")

    print("--- 1. Invoking setup_agent_graph ---")
    print(f"File Path: {initial_state['file_path']}")
    print(f"Template ID: {initial_state['template_id']}")
    
    try:
        with TokenTracker() as tracker:
            output = setup_agent_graph.invoke(initial_state)
        
        print("\n--- 2. Graph execution completed ---")
        print(f"Final error state: {output.get('error')}")
        print(f"Keys returned in output state: {list(output.keys())}")
        
        # Display token usage summary
        tracker.print_summary()

        if output.get("error"):
            print(f"Execution failed with error: {output['error']}")
        else:
            print("Graph ran successfully! Reconstructed blueprint has been generated, merged, and uploaded.")
            
    except Exception as e:
        print(f"Failed during setup_agent_graph invocation: {e}")


if __name__ == "__main__":
    main()
