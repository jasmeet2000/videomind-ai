from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities import SearchResult, TranscriptChunk
from app.domain.interfaces import ITranscriptRepository, IVectorRepository
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever


@pytest.fixture
def mock_vector_repo():
    repo = MagicMock(spec=IVectorRepository)
    repo.search = AsyncMock()
    return repo


@pytest.fixture
def mock_transcript_repo():
    repo = MagicMock(spec=ITranscriptRepository)
    repo.get_by_video_id = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_dense_retriever_delegates(mock_vector_repo):
    retriever = DenseRetriever(vector_repo=mock_vector_repo, collection="test_col")

    mock_vector_repo.search.return_value = [
        SearchResult(
            chunk_id="1",
            video_id="v1",
            modality="speech",
            text="hello",
            score=0.9,
            start_seconds=0,
            end_seconds=1,
            metadata={},
        )
    ]

    results = await retriever.search(query_vector=[0.1, 0.2], video_id="v1", top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == "1"
    mock_vector_repo.search.assert_called_once_with(
        query_vector=[0.1, 0.2], collection="test_col", video_id="v1", top_k=5
    )


@pytest.mark.asyncio
async def test_sparse_retriever_scores_correctly(mock_transcript_repo):
    try:
        from app.retrieval.sparse import BM25SparseRetriever
    except ImportError:
        pytest.skip("rank_bm25 not installed")

    retriever = BM25SparseRetriever(transcript_repo=mock_transcript_repo)

    chunks = [
        TranscriptChunk(
            id="c1", video_id="v1", text="the quick brown fox", start_seconds=0, end_seconds=1
        ),
        TranscriptChunk(
            id="c2", video_id="v1", text="jumps over the lazy dog", start_seconds=1, end_seconds=2
        ),
        TranscriptChunk(
            id="c3",
            video_id="v1",
            text="a completely unrelated sentence",
            start_seconds=2,
            end_seconds=3,
        ),
    ]
    mock_transcript_repo.get_by_video_id.return_value = chunks

    results = await retriever.search(query="fox", video_id="v1", top_k=2)

    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].score > 0
    mock_transcript_repo.get_by_video_id.assert_called_once_with("v1")


@pytest.mark.asyncio
async def test_hybrid_retriever_rrf_fusion(mock_vector_repo, mock_transcript_repo):
    try:
        from app.retrieval.sparse import BM25SparseRetriever
    except ImportError:
        pytest.skip("rank_bm25 not installed")

    dense = DenseRetriever(vector_repo=mock_vector_repo, collection="test")
    sparse = BM25SparseRetriever(transcript_repo=mock_transcript_repo)
    hybrid = HybridRetriever(dense_retriever=dense, sparse_retriever=sparse, rrf_k=1)

    # Dense results: c1 (rank 1), c2 (rank 2)
    mock_vector_repo.search.return_value = [
        SearchResult(
            chunk_id="c1",
            video_id="v1",
            modality="speech",
            text="dense1",
            score=0.9,
            start_seconds=0,
            end_seconds=1,
            metadata={},
        ),
        SearchResult(
            chunk_id="c2",
            video_id="v1",
            modality="speech",
            text="dense2",
            score=0.8,
            start_seconds=1,
            end_seconds=2,
            metadata={},
        ),
    ]

    # Sparse results: c2 (rank 1), c3 (rank 2)
    mock_transcript_repo.get_by_video_id.return_value = [
        TranscriptChunk(
            id="c2", video_id="v1", text="sparse match match here", start_seconds=1, end_seconds=2
        ),
        TranscriptChunk(
            id="c3", video_id="v1", text="another match here", start_seconds=2, end_seconds=3
        ),
    ]

    results = await hybrid.search(query="match", query_vector=[0.1], video_id="v1", top_k=10)

    print("HYBRID RESULTS:", [(r.chunk_id, r.score) for r in results])
    assert len(results) == 3
    # c2 is in both: dense rank 2 (1/(1+2) = 1/3), sparse rank 1 (1/(1+1) = 1/2) -> total 5/6 = 0.833
    # c1 is in dense: rank 1 (1/(1+1) = 1/2) -> 0.5
    # c3 is in sparse: rank 2 (1/(1+2) = 1/3) -> 0.333

    assert results[0].chunk_id == "c2"
    assert results[1].chunk_id == "c1"
    assert results[2].chunk_id == "c3"


def test_cross_encoder_reranker():
    try:
        import sentence_transformers  # noqa

        from app.retrieval.reranker import CrossEncoderReranker
    except ImportError:
        pytest.skip("sentence-transformers not installed")

    reranker = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Mock the internal model to avoid downloading
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.1, 0.9, 0.5]
    reranker._model = mock_model

    results = [
        SearchResult(
            chunk_id="c1",
            video_id="v1",
            modality="speech",
            text="bad match",
            score=0.9,
            start_seconds=0,
            end_seconds=1,
            metadata={},
        ),
        SearchResult(
            chunk_id="c2",
            video_id="v1",
            modality="speech",
            text="perfect match",
            score=0.8,
            start_seconds=1,
            end_seconds=2,
            metadata={},
        ),
        SearchResult(
            chunk_id="c3",
            video_id="v1",
            modality="speech",
            text="okay match",
            score=0.7,
            start_seconds=2,
            end_seconds=3,
            metadata={},
        ),
    ]

    reranked = reranker.rerank(query="perfect", results=results, top_k=2)

    assert len(reranked) == 2
    assert reranked[0].chunk_id == "c2"  # highest score 0.9
    assert reranked[1].chunk_id == "c3"  # score 0.5


def test_cross_encoder_reranker_empty_results():
    try:
        from app.retrieval.reranker import CrossEncoderReranker
    except ImportError:
        pytest.skip("sentence-transformers not installed")

    reranker = CrossEncoderReranker()
    assert reranker.rerank("query", []) == []


def test_cross_encoder_reranker_import_error():
    from unittest.mock import patch

    from app.retrieval.reranker import CrossEncoderReranker

    reranker = CrossEncoderReranker()

    with (
        patch(
            "builtins.__import__",
            side_effect=ImportError("No module named 'sentence_transformers'"),
        ),
        pytest.raises(RuntimeError, match="sentence-transformers not installed"),
    ):
        reranker._ensure_model()


def test_cross_encoder_reranker_general_error():
    from unittest.mock import patch

    from app.retrieval.reranker import CrossEncoderReranker

    reranker = CrossEncoderReranker()

    with patch("builtins.__import__", side_effect=Exception("Unexpected error")):
        with pytest.raises(Exception, match="Unexpected error"):
            reranker._ensure_model()
