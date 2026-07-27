from langchain_groq import ChatGroq

from app.config import settings


def get_llm() -> ChatGroq:
    """
    Return the configured AgentCare language model.

    The provider is centralized here so agents do not depend directly
    on provider-specific configuration.
    """

    if settings.llm_provider.lower() != "groq":
        raise ValueError(
            f"Unsupported LLM provider: {settings.llm_provider}"
        )

    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add it to your local .env file."
        )

    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=0,
        max_retries=2,
    )