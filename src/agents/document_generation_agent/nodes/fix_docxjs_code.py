# src/agents/document_generation_agent/nodes/fix_docxjs_code.py

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.llm.llm import (
    get_llm,
)

from src.agents.document_generation_agent.prompts.fix_docxjs_code_prompt import (
    create_fix_docxjs_code_prompt,
)


async def fix_docxjs_code(
    state: AgentState,
) -> AgentState:

    try:

        prompt = create_fix_docxjs_code_prompt(
            generated_code=state[
                "generated_docxjs_code"
            ],
            validation_error=state[
                "error"
            ],
        )

        llm = get_llm()

        response = await llm.ainvoke(
            prompt,
        )

        fixed_code = getattr(
            response,
            "content",
            str(response),
        )

        return {
            **state,
            "generated_docxjs_code": fixed_code,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }