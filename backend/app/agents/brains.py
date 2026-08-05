"""The agent brains — typed LLM calls with a fallback chain.

Tooling-Guide compliance: the runtime brains are Gemini, Groq and Ollama only.
Claude and ChatGPT are approved as *coding assistants*, never as the product's
agent brain, so nothing here calls them (docs/09 D16).

Why a chain rather than one model:

    gemini       deliberate reasoning  (Flash: risk classification, interpretation)
    gemini_fast  low-latency reasoning (Flash-Lite: the checkout hot path, and a
                 separate quota, so a rate limit on one model does not stop both)
    groq         low-latency reasoning (approved and integrated, but returns HTTP
                 403 "access denied" from our region — see docs/09 D26)
    ollama       local, offline        (survives dead venue wi-fi / rate limits)
    heuristic    deterministic rules   (last resort: the demo still runs)

The heuristic is *not* the product — it is graceful degradation, and every
result records which brain produced it so the UI can label it honestly rather
than implying an LLM answered when one did not.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

GEMINI_MODEL = "gemini-flash-latest"
"""A moving alias on purpose. Pinning `gemini-2.5-flash` failed with "no longer
available to new users" — a pinned model can be retired out from under a new
API key, and a demo that breaks on model retirement is a demo that breaks."""

GEMINI_FAST_MODEL = "gemini-flash-lite-latest"
"""The low-latency tier. Two jobs at once: it keeps the fast/deliberate split
that Groq was meant to provide, and it draws on a different model quota, so a
rate limit on Flash does not take the whole agent down."""

GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_MODEL = "llama3.1:8b"


@dataclass(frozen=True)
class BrainResult:
    """A typed answer plus provenance: which brain produced it, and how."""

    output: BaseModel
    brain: str
    """'gemini' | 'groq' | 'ollama' | 'heuristic'."""
    degraded: bool = False
    """True when no LLM answered and deterministic rules stood in."""
    error: str | None = None


class BrainRouter:
    """Tries each configured brain in order, then falls back to a heuristic."""

    def __init__(self, *, prefer: str | None = None) -> None:
        self.prefer = prefer
        self._agents: dict[str, Any] = {}
        self._dead: dict[str, str] = {}
        """Brains that already failed this run, with the reason.

        Without this, every agent step re-tries every dead brain and pays its
        timeout again: the first end-to-end run spent 10-20 seconds per node
        discovering the same three failures. A brain that fails once is skipped
        for the rest of the process — a demo cannot afford to rediscover an
        outage six times.
        """

    # ------------------------------------------------------------------ setup
    def configured(self) -> list[str]:
        """Every brain this environment could use, in preference order."""
        chain: list[str] = []
        if settings.gemini_api_key:
            chain.extend(["gemini", "gemini_fast"])
        if settings.groq_api_key:
            chain.append("groq")
        chain.append("ollama")  # local; may or may not be running

        if self.prefer and self.prefer in chain:
            chain.remove(self.prefer)
            chain.insert(0, self.prefer)
        return chain

    def available(self) -> list[str]:
        """Brains still worth trying (dead ones dropped)."""
        return [b for b in self.configured() if b not in self._dead]

    @property
    def dead(self) -> dict[str, str]:
        return dict(self._dead)

    @staticmethod
    def _is_permanent(exc: Exception) -> bool:
        """Is this brain broken, or just busy?

        A wrong key, a retired model or a blocked region will fail identically
        forever, so that brain should be skipped for the rest of the run. A
        timeout or a rate limit is temporary and must not disqualify a brain
        that is simply under load.
        """
        status = getattr(exc, "status_code", None)
        if status in {400, 401, 403, 404}:
            return True
        text = f"{type(exc).__name__}: {exc}".lower()
        permanent_markers = (
            "api key",
            "not_found",
            "no longer available",
            "access denied",
            "permission",
            "unauthorized",
        )
        return any(marker in text for marker in permanent_markers)

    def _build_agent(self, brain: str, output_type: type[T], instructions: str) -> Any:
        from pydantic_ai import Agent

        if brain in {"gemini", "gemini_fast"}:
            from pydantic_ai.models.google import GoogleModel
            from pydantic_ai.providers.google import GoogleProvider

            model: Any = GoogleModel(
                GEMINI_MODEL if brain == "gemini" else GEMINI_FAST_MODEL,
                provider=GoogleProvider(api_key=settings.gemini_api_key),
            )
        elif brain == "groq":
            from pydantic_ai.models.groq import GroqModel
            from pydantic_ai.providers.groq import GroqProvider

            model = GroqModel(GROQ_MODEL, provider=GroqProvider(api_key=settings.groq_api_key))
        elif brain == "ollama":
            # Ollama exposes an OpenAI-compatible endpoint; no key needed.
            from pydantic_ai.models.openai import OpenAIChatModel
            from pydantic_ai.providers.openai import OpenAIProvider

            model = OpenAIChatModel(
                OLLAMA_MODEL,
                provider=OpenAIProvider(
                    base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
                    api_key="ollama",
                ),
            )
        else:  # pragma: no cover - guarded by available()
            raise ValueError(f"unknown brain: {brain}")

        return Agent(model, output_type=output_type, instructions=instructions)

    # -------------------------------------------------------------------- run
    async def think(
        self,
        *,
        instructions: str,
        prompt: str,
        output_type: type[T],
        heuristic: T,
    ) -> BrainResult:
        """Ask the first brain that answers; fall back to `heuristic`.

        `heuristic` is required, not optional: every agent step must have a
        deterministic answer available, or a dead network becomes a dead demo.
        """
        errors: list[str] = []

        for brain in self.available():
            for attempt in (1, 2):
                try:
                    key = f"{brain}:{output_type.__name__}"
                    if key not in self._agents:
                        self._agents[key] = self._build_agent(brain, output_type, instructions)
                    result = await self._agents[key].run(prompt)
                    return BrainResult(output=result.output, brain=brain)
                except Exception as exc:  # any brain failure falls through to the next
                    message = f"{brain}: {type(exc).__name__}: {exc}"
                    permanent = self._is_permanent(exc)
                    if permanent:
                        self._dead[brain] = message
                        logger.warning("brain disabled for this run - %s", message)
                        errors.append(message)
                        break
                    if attempt == 1:
                        logger.info("brain busy, retrying once - %s", message)
                        await asyncio.sleep(1.5)
                        continue
                    logger.warning("brain unavailable, falling through - %s", message)
                    errors.append(message)

        return BrainResult(
            output=heuristic,
            brain="heuristic",
            degraded=True,
            error="; ".join(errors) or "; ".join(self._dead.values()) or "no brain configured",
        )
