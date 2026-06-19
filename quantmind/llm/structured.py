"""QuantMind v2 — structured-output helper (graceful degradation).

The canonical pattern every agent uses: try structured output bound to a Pydantic
schema; if the model/provider can't do it, fall back to free text so the pipeline
never blocks. Async-first to match the rest of QuantMind.
"""
from typing import Any, Callable

from quantmind.utils import logger


def bind_structured(llm: Any, schema: Any, agent_name: str) -> Any | None:
    """Return a structured-output runnable, or None if the model can't do it."""
    try:
        return llm.with_structured_output(schema)
    except (NotImplementedError, AttributeError) as exc:
        logger.warning("{}: no structured output ({}); will use free text", agent_name, exc)
        return None


async def ainvoke_structured_or_freetext(
    structured_llm: Any,
    plain_llm: Any,
    prompt: Any,
    render: Callable[[Any], str],
    agent_name: str,
) -> str:
    """Invoke the structured LLM (rendering its result) or fall back to free text."""
    if structured_llm is not None:
        try:
            return render(await structured_llm.ainvoke(prompt))
        except Exception as exc:  # noqa: BLE001 — degrade on any structured failure
            logger.warning(
                "{}: structured call failed ({}); retrying as free text", agent_name, exc
            )
    response = await plain_llm.ainvoke(prompt)
    return response.content
