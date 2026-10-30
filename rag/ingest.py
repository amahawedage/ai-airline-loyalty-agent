import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

KB_DIR = BASE_DIR / "knowledge_base" / "raw"
VECTOR_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "airline_loyalty_kb"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# Set to True only when you intentionally want to rebuild
# the existing ChromaDB index from source documents.
REBUILD_INDEX = False


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    dotenv_path=BASE_DIR / ".env",
    override=False
)


def get_gemini_api_key():
    """
    Retrieve Gemini API key from environment variables.
    Works locally and with Streamlit Community Cloud secrets.
    """

    api_key = (
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "Gemini API key not found. "
            "Configure GOOGLE_API_KEY in .env "
            "or Streamlit Cloud secrets."
        )

    return api_key


# ============================================================
# 3. LOAD KNOWLEDGE-BASE DOCUMENTS
# ============================================================

def load_documents():
    """
    Load airline loyalty knowledge-base text documents.
    """

    documents = []

    if not KB_DIR.exists():
        raise FileNotFoundError(
            f"Knowledge-base directory not found: {KB_DIR}"
        )

    for file_path in sorted(KB_DIR.glob("*.txt")):

        text = file_path.read_text(encoding="utf-8")

        if not text.strip():
            print(f"Skipping empty file: {file_path.name}")
            continue

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "topic": file_path.stem
            }
        )

        documents.append(document)

    return documents


# ============================================================
# 4. INITIALIZE GEMINI EMBEDDINGS
# ============================================================

def get_embeddings():
    """
    Initialize Gemini embedding model.
    """

    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=get_gemini_api_key()
    )


# ============================================================
# 5. CREATE CHROMADB VECTOR STORE
# ============================================================

def create_vector_store(chunks):
    """
    Create or populate ChromaDB using Gemini embeddings.
    """

    if VECTOR_DIR.exists() and REBUILD_INDEX:
        print("Removing previous ChromaDB index...")
        shutil.rmtree(VECTOR_DIR)

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DIR)
    )

    # Avoid adding the same knowledge-base chunks repeatedly.
    existing_count = vector_store._collection.count()

    if existing_count > 0:
        raise RuntimeError(
            f"ChromaDB collection already contains "
            f"{existing_count} records. "
            "To rebuild it, set REBUILD_INDEX = True "
            "after confirming the index is regenerable."
        )

    vector_store.add_documents(chunks)

    return vector_store


# ============================================================
# 6. MAIN INGESTION PROCESS
# ============================================================

def main():

    print("\n======================================")
    print("AIRLINE LOYALTY RAG INGESTION")
    print("======================================")

    try:

        print("\nLoading knowledge-base documents...")

        documents = load_documents()

        print(f"Documents loaded: {len(documents)}")

        if not documents:
            print(
                "ERROR: No knowledge-base documents found."
            )
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(documents)

        print(f"Chunks created: {len(chunks)}")

        print("\nCreating Gemini embeddings and ChromaDB...")

        create_vector_store(chunks)

        print("\nRAG ingestion completed successfully.")

        print(f"ChromaDB location: {VECTOR_DIR}")

        print(f"Embedding model: {EMBEDDING_MODEL}")

    except Exception as error:

        print("\nRAG ingestion failed.")

        print(f"Error type: {type(error).__name__}")

        print(f"Error message: {error}")


# ============================================================
# 7. RUN INGESTION
# ============================================================

if __name__ == "__main__":
    main()