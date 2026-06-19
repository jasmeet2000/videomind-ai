"""
VideoMind AI — LLM Service (Ollama Client)
============================================
Communicates with a local Ollama instance for LLM generation.
"""

import logging

import httpx

from app.domain.interfaces import ILLMBackend

logger = logging.getLogger(__name__)


class OllamaClient(ILLMBackend):
    """Client for generating responses using a local Ollama instance."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen3") -> None:
        self.host = host.rstrip("/")
        self.model = model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate a response via the Ollama /api/generate endpoint.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=120.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.RequestError as e:
            logger.error(f"Failed to communicate with Ollama at {self.host}: {e}")
            raise RuntimeError("LLM generation failed due to network error.") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama returned an error status: {e.response.status_code}")
            raise RuntimeError(f"LLM generation failed with status {e.response.status_code}") from e
