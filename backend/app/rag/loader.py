from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader

def load_documents():
    
    # docs를 찾는 코드
    docs_path = Path(__file__).resolve().parents[3] / "docs"
    documents = []
    pdf_files = list(docs_path.rglob("*.pdf")) 
    # rglob("*.pdf")는 KDCA, SOP, CDC 각각의 폴더 안에 있는 PDF를 전부 찾아줌

    for pdf in pdf_files:
        print(f"Loading: {pdf.name}")
        loader = PyPDFLoader(str(pdf))
        documents.extend(loader.load())
    return documents