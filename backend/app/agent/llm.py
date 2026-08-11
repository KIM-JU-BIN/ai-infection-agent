from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

# backend/.env 로드
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)