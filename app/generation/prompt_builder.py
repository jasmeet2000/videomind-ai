"""
VideoMind AI — Prompt Builder (Builder Pattern)
=================================================
Assembles LLM prompts step-by-step from retrieved context chunks.

DESIGN PATTERN — Builder:
    Complex prompt construction is broken into discrete, chainable steps:
    set_system_instruction → add_context_chunks → set_user_query → build().
    This avoids one massive string-formatting function and makes each
    component independently testable.

SOLID — Single Responsibility:
    Only builds prompts. Does not call the LLM or retrieve chunks.
"""

from __future__ import annotations

from app.domain.entities import SearchResult

# Stub — implementation in Phase 8


class PromptBuilder:
    """
    Fluent builder for assembling RAG prompts from retrieved context.

    Usage:
        prompt = (
            PromptBuilder()
            .set_system_instruction("You are a helpful video assistant.")
            .add_context_chunks(results)
            .set_user_query("When did the instructor explain transformers?")
            .build()
        )
    """

    def __init__(self) -> None:
        self._system: str = ""
        self._context_chunks: list[SearchResult] = []
        self._user_query: str = ""

    def set_system_instruction(self, instruction: str) -> "PromptBuilder":
        """Set the system-level instruction for the LLM."""
        self._system = instruction
        return self

    def add_context_chunks(self, chunks: list[SearchResult]) -> "PromptBuilder":
        """Add retrieved context chunks to the prompt."""
        self._context_chunks = chunks
        return self

    def set_user_query(self, query: str) -> "PromptBuilder":
        """Set the user's natural language query."""
        self._user_query = query
        return self

    def build(self) -> str:
        """
        Assemble and return the final prompt string.

        Returns:
            Fully assembled prompt ready for LLM generation.

        Raises:
            PromptBuildError: If required fields are missing.
        """
        raise NotImplementedError("Phase 8: Implement prompt template assembly")
