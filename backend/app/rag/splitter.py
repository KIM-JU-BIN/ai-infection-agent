from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents):
    """
    PDF 문서를 검색하기 좋은 크기로 분할
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, # 약 800자로 자름
        chunk_overlap=150, # 앞뒤 200자 겹치게
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(documents)

    return chunks