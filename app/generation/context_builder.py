"""
VideoMind AI — Context Builder
================================
Assembles retrieved SearchResult chunks into a structured context string
for LLM consumption, with timestamp annotations and source attribution.

SOLID — Single Responsibility:
    Only builds the context string from results. Does not call the LLM.
"""

from __future__ import annotations

from app.domain.entities import SearchResult

# Stub — implementation in Phase 8


class ContextBuilder:
    """
    Assembles retrieved chunks into a human-readable LLM context block.
    """

    def build(self, results: list[SearchResult], max_chunks: int = 8) -> str:
        """
        Format retrieved chunks with timestamps and modality labels.

        Args:
            results: List of SearchResult from the retrieval pipeline.
            max_chunks: Maximum number of chunks to include.

        Returns:
            Formatted context string for inclusion in the LLM prompt.
        """
        raise NotImplementedError("Phase 8: Implement context assembly with timestamps")
