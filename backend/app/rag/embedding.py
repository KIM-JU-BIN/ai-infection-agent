from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings

# backend/.env 로드
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)