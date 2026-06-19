import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.domain.entities import SearchResult
from app.generation.context_builder import ContextBuilder
from app.generation.prompt_builder import PromptBuilder
from app.generation.llm_service import OllamaClient
from app.use_cases.chat_with_video import ChatWithVideoUseCase


def test_context_builder_formats_and_truncates():
    builder = ContextBuilder(max_tokens=20) # Very low token limit to test truncation
    
    # words_per_token is 0.75, so 20 tokens = 15 words
    results = [
        SearchResult(chunk_id="1", video_id="v1", modality="speech", text="this is a short test sentence", score=0.9, start_seconds=10, end_seconds=15, metadata={}),
        SearchResult(chunk_id="2", video_id="v1", modality="vision", text="this is a much longer test sentence that will be truncated", score=0.8, start_seconds=20, end_seconds=25, metadata={}),
    ]
    
    context = builder.build_context(results)
    
    assert "[00:10 - 00:15] (SPEECH): this is a short test sentence" in context
    assert "[00:20 - 00:25] (VISION): this is a much longer test sentence that will be truncated" not in context
    
def test_context_builder_empty():
    builder = ContextBuilder()
    assert builder.build_context([]) == "No relevant video content found."


def test_prompt_builder():
    builder = PromptBuilder()
    sys_prompt = builder.build_system_prompt()
    assert "You are an AI assistant" in sys_prompt
    
    user_prompt = builder.build_user_prompt("What is this?", "Context text")
    assert "<context>" in user_prompt
    assert "Context text" in user_prompt
    assert "Question: What is this?" in user_prompt


@pytest.mark.asyncio
async def test_ollama_client_success():
    client = OllamaClient()
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "This is the generated text"}
    mock_response.raise_for_status = MagicMock()
    
    mock_post = AsyncMock(return_value=mock_response)
    
    with patch("httpx.AsyncClient.post", mock_post):
        response = await client.generate("Hello", "System prompt")
        assert response == "This is the generated text"
        mock_post.assert_called_once()
        
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["prompt"] == "Hello"
        assert kwargs["json"]["system"] == "System prompt"


@pytest.mark.asyncio
async def test_ollama_client_failure():
    client = OllamaClient()
    
    mock_post = AsyncMock(side_effect=httpx.RequestError("Network error"))
    
    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(RuntimeError, match="network error"):
            await client.generate("Hello")


@pytest.mark.asyncio
async def test_chat_with_video_usecase():
    mock_embedding = MagicMock()
    mock_embedding.encode.return_value = [0.1, 0.2]
    
    mock_retriever = AsyncMock()
    # Hybrid retriever returns candidates
    mock_retriever.search.return_value = [
        SearchResult(chunk_id="1", video_id="v1", modality="speech", text="candidate 1", score=0.9, start_seconds=0, end_seconds=1, metadata={})
    ]
    
    mock_reranker = MagicMock()
    # Reranker returns reranked candidates
    mock_reranker.rerank.return_value = [
        SearchResult(chunk_id="1", video_id="v1", modality="speech", text="candidate 1", score=0.9, start_seconds=0, end_seconds=1, metadata={})
    ]
    
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "The answer is candidate 1"
    
    usecase = ChatWithVideoUseCase(
        embedding_model=mock_embedding,
        retriever=mock_retriever,
        reranker=mock_reranker,
        llm_backend=mock_llm,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
    )
    
    result = await usecase.execute(video_id="v1", query="test query", top_k=1)
    
    assert result["answer"] == "The answer is candidate 1"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["chunk_id"] == "1"
    
    # Verify the workflow
    mock_embedding.encode.assert_called_once_with("test query")
    mock_retriever.search.assert_called_once_with(query="test query", query_vector=[0.1, 0.2], video_id="v1", top_k=2)
    mock_reranker.rerank.assert_called_once()
    mock_llm.generate.assert_called_once()
