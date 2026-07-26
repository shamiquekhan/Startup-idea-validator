"""LLM provider config — tries Groq first, falls back to Gemini, then Ollama."""

import logging
import os
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def get_llm(model: str = "qwen3:1.7b", temperature: float = 0.1, num_predict: int = 512) -> BaseChatModel:
    provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "groq":
        return _try_groq(temperature, num_predict)

    if provider == "gemini":
        return _try_gemini(temperature, num_predict)

    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, temperature=temperature, num_predict=num_predict)


def _try_groq(temperature: float, num_predict: int) -> BaseChatModel:
    from langchain_groq import ChatGroq
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    return ChatGroq(
        model=groq_model,
        temperature=temperature,
        max_tokens=num_predict,
        api_key=os.environ.get("GROQ_API_KEY"),
    )


def _try_gemini(temperature: float, num_predict: int) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    return ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=temperature,
        max_output_tokens=num_predict,
        google_api_key=os.environ.get("GEMINI_API_KEY"),
    )


def get_llm_with_fallback(model: str = "qwen3:1.7b", temperature: float = 0.1, num_predict: int = 512) -> BaseChatModel:
    provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "gemini":
        try:
            return _try_gemini(temperature, num_predict)
        except Exception:
            logger.warning("Gemini call failed, falling back to Ollama")
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model, temperature=temperature, num_predict=num_predict)

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature, num_predict=num_predict)

    try:
        return _try_groq(temperature, num_predict)
    except Exception:
        logger.warning("Groq call failed, trying Gemini")
        try:
            return _try_gemini(temperature, num_predict)
        except Exception:
            logger.warning("Gemini call also failed, falling back to Ollama")
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model, temperature=temperature, num_predict=num_predict)
