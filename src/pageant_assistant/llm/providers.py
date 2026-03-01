"""LLM provider: requests-based Groq chat client.

Uses ``requests`` (urllib3) instead of the Groq SDK (httpx) because httpx
fails on Streamlit Community Cloud with Python 3.13.  The ``RequestsGroqChat``
class exposes the same ``.invoke(prompt)`` interface that LangChain's
``ChatGroq`` provides, so all graph nodes work without changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests as _req

from pageant_assistant.config.settings import GROQ_API_KEY, GROQ_MODEL, TEMPERATURE

_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class _AIMessage:
    """Minimal stand-in for ``langchain_core.messages.AIMessage``."""

    content: str


class RequestsGroqChat:
    """Drop-in replacement for ``ChatGroq`` using raw HTTP via ``requests``.

    Only implements ``.invoke(prompt)`` — the single method used by every
    graph node and RAG helper.
    """

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_retries = max_retries

    def invoke(self, prompt: str | Any) -> _AIMessage:
        """Send a single-turn chat completion and return an ``_AIMessage``.

        Args:
            prompt: The user prompt string (or any object whose ``str()``
                    representation is the prompt).

        Returns:
            ``_AIMessage`` with a ``.content`` attribute holding the assistant
            reply text.

        Raises:
            requests.HTTPError: On non-2xx Groq API responses after retries.
        """
        text = str(prompt)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text}],
            "temperature": self.temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_exc: Exception | None = None
        for _attempt in range(self.max_retries):
            try:
                resp = _req.post(
                    _GROQ_CHAT_URL,
                    json=payload,
                    headers=headers,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return _AIMessage(content=content)
            except (_req.ConnectionError, _req.Timeout) as exc:
                last_exc = exc
                continue
            except _req.HTTPError:
                raise

        raise ConnectionError(
            f"Failed to connect to Groq after {self.max_retries} attempts: {last_exc}"
        )


def get_llm(
    role: str = "drafting",
    model: str | None = None,
    temperature: float | None = None,
) -> RequestsGroqChat:
    """Create a Groq LLM client configured for a specific agent role.

    Args:
        role: Agent role key from TEMPERATURE dict (e.g. "drafting", "critic").
              Determines the default temperature.
        model: Override the default model.
        temperature: Override the role-based default temperature.

    Raises:
        OSError: If GROQ_API_KEY is not set.
    """
    if not GROQ_API_KEY:
        raise OSError("GROQ_API_KEY is not set. Add it to your .env file in the project root.")
    return RequestsGroqChat(
        model=model or GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature if temperature is not None else TEMPERATURE.get(role, 0.7),
        max_retries=3,
    )
