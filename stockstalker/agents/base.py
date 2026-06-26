"""StockStalker v2 — agent base framework.

A minimal custom framework (no CrewAI/LangGraph): every agent is an async class
with a single ``run(context)`` method returning a typed ``AgentResult``. Callers
use ``execute()``, which wraps ``run()`` with timing, logging, and a persisted
run record — and never raises, so one agent's failure can't abort the pipeline.

Dependencies (llm, db, vector_store) are always injected, never constructed here.
"""
import asyncio
from abc import ABC, abstractmethod

from stockstalker.llm import GeminiClient
from stockstalker.memory import DatabaseManager, VectorStore
from stockstalker.schemas import AgentContext, AgentResult
from stockstalker.utils import logger


class BaseAgent(ABC):
    """Abstract base for every agent."""

    def __init__(
        self,
        name: str,
        llm: GeminiClient,
        db: DatabaseManager,
        vector_store: VectorStore,
    ) -> None:
        # All dependencies are injected from outside — never instantiated here.
        self.name = name
        self.llm = llm
        self.db = db
        self.vector_store = vector_store

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Agent-specific logic. Implemented by every subclass."""

    async def execute(self, context: AgentContext) -> AgentResult:
        """Run the agent with timing, logging, and a persisted run record.

        Always returns an AgentResult (never raises) so a single agent failure
        does not abort the orchestrator.
        """
        start_time = asyncio.get_event_loop().time()
        logger.info("[{}] Starting for ticker: {}", self.name, context.ticker)

        try:
            result = await self.run(context)
        except Exception as exc:  # noqa: BLE001 — agent failures are captured, not raised
            logger.error("[{}] error ({}): {}", self.name, type(exc).__name__, exc)
            result = AgentResult(
                agent_name=self.name,
                success=False,
                data=None,
                error=str(exc),
                duration_seconds=0.0,
            )

        duration = asyncio.get_event_loop().time() - start_time
        result.duration_seconds = duration
        logger.info(
            "[{}] {} in {:.2f}s",
            self.name,
            "OK" if result.success else "FAILED",
            duration,
        )

        await self.db.log_agent_run(
            ticker=context.ticker,
            agent_name=self.name,
            duration=duration,
            success=result.success,
            error=result.error,
        )
        return result
