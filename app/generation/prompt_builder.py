"""
VideoMind AI — Prompt Builder
===============================
Constructs prompts for the LLM using the generated context and user query.
"""

class PromptBuilder:
    """Templates and builds prompts for Retrieval-Augmented Generation."""

    def __init__(self, system_prompt: str = None) -> None:
        self.system_prompt = system_prompt or (
            "You are an AI assistant that answers questions about a video. "
            "You will be provided with a chronological context of transcripts and visual cues extracted from the video.\n"
            "Your task is to answer the user's question based strictly on this provided context.\n"
            "If the answer cannot be found in the context, clearly state that you don't know based on the video.\n"
            "Do not make up information. Use timecodes in your answer if relevant."
        )

    def build_system_prompt(self) -> str:
        """Returns the system instruction."""
        return self.system_prompt

    def build_user_prompt(self, query: str, context: str) -> str:
        """
        Combines the retrieved context and the user query.
        """
        return (
            f"Here is the context extracted from the video:\n\n"
            f"<context>\n"
            f"{context}\n"
            f"</context>\n\n"
            f"Question: {query}\n"
            f"Answer:"
        )
