"""
VideoMind AI — Chat with Video Use Case
========================================
Orchestrates Retrieval-Augmented Generation (RAG) by combining
the Retrieval layer and the LLM Generation layer.
"""

from typing import Dict, Any

from app.domain.interfaces import IEmbeddingModel, IHybridRetriever, IReranker, ILLMBackend
from app.generation.context_builder import ContextBuilder
from app.generation.prompt_builder import PromptBuilder


class ChatWithVideoUseCase:
    """End-to-end use case for chatting with a specific video."""

    def __init__(
        self,
        embedding_model: IEmbeddingModel,
        retriever: IHybridRetriever,
        reranker: IReranker,
        llm_backend: ILLMBackend,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
    ) -> None:
        self.embedding_model = embedding_model
        self.retriever = retriever
        self.reranker = reranker
        self.llm_backend = llm_backend
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder

    async def execute(self, video_id: str, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Execute the RAG pipeline.

        Args:
            video_id: The ID of the video to chat with.
            query: The user's question.
            top_k: Number of retrieved chunks to consider.

        Returns:
            A dictionary containing the generated answer and cited sources.
        """
        # 1. Embed the query
        query_vector = self.embedding_model.encode(query)

        # 2. Retrieve candidate chunks
        candidate_results = await self.retriever.search(
            query=query,
            query_vector=query_vector,
            video_id=video_id,
            top_k=top_k * 2,  # Over-fetch for reranker
        )

        # 3. Rerank candidates
        if candidate_results:
            reranked_results = self.reranker.rerank(
                query=query,
                results=candidate_results,
                top_k=top_k,
            )
        else:
            reranked_results = []

        # 4. Build context
        context_str = self.context_builder.build_context(reranked_results)

        # 5. Build prompt
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(query=query, context=context_str)

        # 6. Generate answer
        answer = await self.llm_backend.generate(prompt=user_prompt, system_prompt=system_prompt)

        return {
            "answer": answer,
            "sources": [
                {
                    "chunk_id": res.chunk_id,
                    "text": res.text,
                    "score": res.score,
                    "start_seconds": res.start_seconds,
                    "end_seconds": res.end_seconds,
                }
                for res in reranked_results
            ],
        }
