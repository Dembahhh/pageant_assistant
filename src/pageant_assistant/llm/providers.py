from langchain_groq import ChatGroq
from pageant_assistant.config.settings import GROQ_API_KEY, GROQ_MODEL, TEMPERATURE


def get_llm(
    role: str = "drafting",
    model: str | None = None,
    temperature: float | None = None,
) -> ChatGroq:
    """Create a Groq LLM client configured for a specific agent role.

    Args:
        role: Agent role key from TEMPERATURE dict (e.g. "drafting", "critic").
              Determines the default temperature.
        model: Override the default model.
        temperature: Override the role-based default temperature.
    """
    return ChatGroq(
        model=model or GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature if temperature is not None else TEMPERATURE.get(role, 0.7),
        max_retries=3,
    )
