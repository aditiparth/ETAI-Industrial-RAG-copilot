import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
#GEMINI_MODEL = "gemini-2.0-flash"
LLM_MODEL = "openai/gpt-oss-20b:free"
TOP_K_RETRIEVE = 15
TOP_K_FINAL = 5