# llm_interface.py: central factory for all LLM clients used by the chatbot.
# Keeping LLM creation here allows consistent control over models, params, and upgrades.

from langchain_google_genai import ChatGoogleGenerativeAI
from .config import GOOGLE_API_KEY, GEMINI_MODEL


def get_main_llm():
    """
    LLM for medical QA (RAG answering).
    - Lower temperature → deterministic, safe outputs.
    - Used by the doc_chain in chatbot.py.
    """
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )


def get_summary_llm():
    """
    LLM for conversation summarization.
    - Lower temperature → stable summaries.
    - Separate instance → allows swapping to cheaper models later.
    """
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1
    )


def get_classifier_llm():
    """
    LLM for input classification (greeting / medical / non-medical).
    - Temperature 0 → fully deterministic categorization.
    """
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0
    )
