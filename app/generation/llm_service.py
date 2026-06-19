"""
VideoMind AI — LLM Service (Ollama Client)
===========================================
Wraps the Ollama HTTP client and exposes a clean generate() interface.

DESIGN PATTERN — Strategy:
    LLMService accepts an ILLMBackend at construction. Swapping from
    Qwen3 to Llama 3.1 or Gemma 3 requires zero changes here.

SOLID — Dependency Inversion:
    Depends on ILLMBackend abstract interface, not on the Ollama client.

SOLID — Single Responsibility:
    Only handles LLM generation. Context assembly is in ContextBuilder.
"""

from __future__ import annotations

from app.domain.interfaces import ILLMBackend

# Stub — implementation in Phase 8


class LLMService:
    """
    Generates natural language responses via a pluggable LLM backend.
    """

    def __init__(self, backend: ILLMBackend) -> None:
        """
        Args:
            backend: An ILLMBackend implementation (e.g., OllamaBackend).
        """
        self.backend = backend

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and return the generated response.

        Args:
            prompt: Fully assembled prompt string from PromptBuilder.

        Returns:
            Generated response text from the LLM.

        Raises:
            LLMUnavailableError: If the backend is unreachable.
        """
        raise NotImplementedError("Phase 8: Implement Ollama generation")
