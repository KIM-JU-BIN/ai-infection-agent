"""
docs 폴더 PDF를 sop_documents 테이블에 적재
"""

import asyncio
import sys
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import delete

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.logging import get_logger
from app.db.models.sop_document import SopDocument
from app.db.session import AsyncSessionLocal
from app.llm.embedding_client import EmbeddingClient


logger = get_logger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"


SOURCE_MAP = {
    "CDC": {
        "source_type": "CDC",
        "authority": "CDC",
    },
    "KDCA": {
        "source_type": "KDCA",
        "authority": "질병관리청",
    },
    "SOP": {
        "source_type": "INTERNAL_SOP",
        "authority": "병원 내부 SOP",
    },
}


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    PDF 텍스트 추출
    """

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.replace('\x00','').strip()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> list[str]:
    """
    텍스트 청크 분할
    """

    cleaned = " ".join(text.split())

    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(cleaned):
        end = start + chunk_size
        chunk = cleaned[start:end].strip()

        if chunk:
            chunks.append(chunk)

        next_start = end - chunk_overlap

        if next_start <= start:
            break

        start = next_start

    return chunks


def infer_disease_type(file_path: Path) -> str | None:
    """
    파일명으로 감염병 유형 추정.
    """

    name = file_path.name.lower()

    if "covid" in name or "코로나" in name:
        return "COVID-19"

    if "influenza" in name or "인플루엔자" in name or "독감" in name:
        return "Influenza"

    return None


async def ingest_pdf(
    *,
    pdf_path: Path,
    source_folder: str,
    embedding_client: EmbeddingClient,
) -> int:
    """
    PDF 1개 적재
    """

    source_info = SOURCE_MAP[source_folder]

    text = extract_text_from_pdf(pdf_path)

    if not text:
        logger.warning(f"텍스트 추출 실패: {pdf_path}")
        return 0

    chunks = chunk_text(text)

    if not chunks:
        logger.warning(f"청크 생성 실패: {pdf_path}")
        return 0

    # [:50]을 사용해 최대 50글자로 안전하게 자름
    document_code = f"{source_folder}-{pdf_path.stem}"[:50]
    title = pdf_path.stem
    disease_type = infer_disease_type(pdf_path)

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(SopDocument).where(
                SopDocument.document_code == document_code,
            )
        )

        inserted_count = 0

        for index, chunk in enumerate(chunks):
            embedding = await embedding_client.embed_text(chunk)

            document = SopDocument(
                document_code=document_code,
                title=title,
                source_type=source_info["source_type"],
                authority=source_info["authority"],
                disease_type=disease_type,
                section=None,
                chunk_index=index,
                content=chunk,
                source_path=str(pdf_path),
                metadata_json={
                    "file_name": pdf_path.name,
                    "source_folder": source_folder,
                },
                embedding=embedding,
            )

            session.add(document)
            inserted_count += 1

        await session.commit()

    logger.info(f"적재 완료: {pdf_path} / {inserted_count}개 청크")
    return inserted_count


async def main() -> None:
    """
    전체 docs 적재.
    """

    if not DOCS_ROOT.exists():
        raise FileNotFoundError(f"docs 폴더가 없습니다: {DOCS_ROOT}")

    embedding_client = EmbeddingClient()

    total_count = 0

    for source_folder in SOURCE_MAP:
        folder_path = DOCS_ROOT / source_folder

        if not folder_path.exists():
            logger.warning(f"폴더 없음: {folder_path}")
            continue

        pdf_files = sorted(folder_path.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"PDF 없음: {folder_path}")
            continue

        for pdf_path in pdf_files:
            count = await ingest_pdf(
                pdf_path=pdf_path,
                source_folder=source_folder,
                embedding_client=embedding_client,
            )
            total_count += count

    logger.info(f"전체 적재 완료. 총 {total_count}개 청크 저장.")


if __name__ == "__main__":
    asyncio.run(main())
