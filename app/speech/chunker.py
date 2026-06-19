from __future__ import annotations

from typing import Callable, List, Optional

from app.core.constants import TRANSCRIPT_CHUNK_MAX_TOKENS, TRANSCRIPT_OVERLAP_TOKENS
from app.core.logging import get_logger
from app.domain.entities import TranscriptChunk

logger = get_logger(__name__)


def _default_token_count(text: str) -> int:
    """Estimate token count for a piece of text.

    Tries to use tiktoken if available; otherwise falls back to a
    conservative character-based estimate (1 token ≈ 4 characters).
    """
    if not text:
        return 0
    try:
        import tiktoken as _tiktoken  # type: ignore

        try:
            enc = _tiktoken.get_encoding("cl100k_base")
        except Exception:
            enc = _tiktoken.encoding_for_model("gpt-4o-mini") if hasattr(_tiktoken, "encoding_for_model") else _tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Fallback heuristic
        return max(1, int(len(text) / 4))


def chunk_transcript_chunks(
    segments: List[TranscriptChunk],
    max_tokens: int = TRANSCRIPT_CHUNK_MAX_TOKENS,
    overlap_tokens: int = TRANSCRIPT_OVERLAP_TOKENS,
    token_counter: Optional[Callable[[str], int]] = None,
) -> List[TranscriptChunk]:
    """
    Merge Whisper segments (TranscriptChunk) into larger chunks bounded by
    an approximate token limit and optional overlap.

    Args:
        segments: Ordered (or unordered) list of TranscriptChunk.
        max_tokens: Maximum tokens per output chunk (approximate).
        overlap_tokens: Number of tokens to overlap between adjacent chunks.
        token_counter: Optional callable to return token count for a string
                       (used for deterministic testing).

    Returns:
        List[TranscriptChunk] where each chunk contains concatenated text and
        the start/end timestamps spanning the original segments.
    """
    if token_counter is None:
        token_counter = _default_token_count

    if not segments:
        return []

    segments_sorted = sorted(segments, key=lambda s: s.start_seconds)
    token_counts = [token_counter(s.text or "") for s in segments_sorted]

    chunks: List[TranscriptChunk] = []
    n = len(segments_sorted)
    i = 0

    while i < n:
        accum_tokens = 0
        j = i
        # Accumulate segments until exceeding max_tokens (but include at least one)
        while j < n:
            seg_tokens = token_counts[j]
            if accum_tokens + seg_tokens > max_tokens and accum_tokens > 0:
                break
            accum_tokens += seg_tokens
            j += 1

        chosen = segments_sorted[i:j] if j > i else [segments_sorted[i]]
        text = " ".join(s.text.strip() for s in chosen if s.text)
        start_sec = chosen[0].start_seconds
        end_sec = chosen[-1].end_seconds
        avg_conf = sum((s.confidence or 0.0) for s in chosen) / len(chosen)
        language = chosen[0].language or (segments_sorted[0].language if segments_sorted else "")

        chunk = TranscriptChunk(
            video_id=chosen[0].video_id,
            text=text,
            start_seconds=start_sec,
            end_seconds=end_sec,
            confidence=avg_conf,
            language=language,
        )
        chunks.append(chunk)

        # If we've consumed all segments, we're done — avoid creating an
        # extra final chunk due to overlap logic.
        if j >= n:
            break

        # Determine next start index with overlap
        if overlap_tokens <= 0:
            next_i = j
        else:
            overlap_needed = overlap_tokens
            k = 0
            for back_idx in range(j - 1, i - 1, -1):
                overlap_needed -= token_counts[back_idx]
                k += 1
                if overlap_needed <= 0:
                    break
            if k == 0:
                next_i = j
            else:
                next_i = j - k
                # Ensure forward progress
                if next_i <= i:
                    next_i = i + 1

        i = next_i

    return chunks
