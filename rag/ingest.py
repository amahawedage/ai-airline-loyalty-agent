from pathlib import Path
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / "knowledge_base" / "raw"
VECTOR_DIR = BASE_DIR / "chroma_db"


def load_documents():
    documents = []

    for file_path in KB_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "topic": file_path.stem
            }
        )

        documents.append(document)

    return documents


def main():
    print("Loading knowledge-base documents...")

    documents = load_documents()

    print(f"Documents loaded: {len(documents)}")

    if not documents:
        print("ERROR: No knowledge-base documents found.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    print(f"Chunks created: {len(chunks)}")

    print("Creating embeddings and ChromaDB...")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    vector_store = Chroma(
        collection_name="airline_loyalty_kb",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DIR)
    )

    vector_store.add_documents(chunks)

    print("RAG ingestion completed successfully.")
    print(f"ChromaDB location: {VECTOR_DIR}")


if __name__ == "__main__":
    main();