"""
VideoMind AI — Context Builder
================================
Takes retrieved SearchResult objects and formats them into a cohesive 
string for the LLM to process.
"""

from app.domain.entities import SearchResult


class ContextBuilder:
    """Formats retrieved chunks into LLM-readable context."""

    def __init__(self, max_tokens: int = 4000) -> None:
        self.max_tokens = max_tokens
        # Very rough approximation: 1 word ≈ 1.3 tokens
        self._words_per_token = 0.75

    def build_context(self, results: list[SearchResult]) -> str:
        """
        Takes a list of SearchResults, sorts them chronologically, 
        deduplicates overlaps, and formats them into a single string.
        """
        if not results:
            return "No relevant video content found."

        # Sort chronologically
        results.sort(key=lambda x: x.start_seconds)

        context_parts = []
        current_words = 0
        max_words = int(self.max_tokens * self._words_per_token)

        for res in results:
            # Format time
            start_m, start_s = divmod(int(res.start_seconds), 60)
            end_m, end_s = divmod(int(res.end_seconds), 60)
            time_str = f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}]"

            modality_str = res.modality.upper()
            content = res.text.strip()
            
            # Simple deduplication could go here (e.g., skip identical content)
            
            chunk_str = f"{time_str} ({modality_str}): {content}"
            chunk_words = len(chunk_str.split())

            if current_words + chunk_words > max_words:
                break

            context_parts.append(chunk_str)
            current_words += chunk_words

        if not context_parts:
            return "No relevant video content found."

        return "\n".join(context_parts)
