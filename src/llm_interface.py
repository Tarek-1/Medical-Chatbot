# llm_interface.py — initializes the Gemini model.

from langchain_google_genai import ChatGoogleGenerativeAI
from .config import GOOGLE_API_KEY, GEMINI_MODEL


def get_llm():
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY)
