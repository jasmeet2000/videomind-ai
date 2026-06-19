"""
VideoMind AI — Use Case: Chat With Video
==========================================
Full RAG query flow: query → embed → retrieve → rerank → build context
→ build prompt → generate → return answer.

Clean Architecture — Application Layer:
    The most complex use case. It composes EmbeddingService, HybridRetriever,
    CrossEncoderReranker, ContextBuilder, PromptBuilder, and LLMService.
    None of those know about each other — coordination happens here.
"""

from __future__ import annotations

# Stub — implementation in Phase 8


class ChatWithVideoUseCase:
    """Answers natural language questions about a video via RAG."""

    async def execute(
        self,
        question: str,
        video_id: str,
    ) -> str:
        """
        Run the full RAG pipeline and return a generated answer.

        Args:
            question: User's natural language question.
            video_id: The target video to query.

        Returns:
            Generated answer string from the LLM.
        """
        raise NotImplementedError("Phase 8: Wire embedding → retrieval → LLM generation")
