# config.py: stores environment variables, API keys, and constants used across modules.
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# API keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

INDEX_NAME = "medical-chatbot"

EMBEDDING_MODEL = "BAAI/bge-m3"

GEMINI_MODEL = "models/gemini-flash-latest"

# Paths
DATA_PATH = "data"
