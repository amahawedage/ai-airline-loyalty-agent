import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "airline_loyalty_kb"

EMBEDDING_MODEL = "models/gemini-embedding-001"


# ============================================================
# 2. LOAD GEMINI API KEY
# ============================================================

# Load environment variables from the project .env file.
# Do not overwrite environment variables already provided
# by Streamlit Community Cloud.

load_dotenv(
    dotenv_path=BASE_DIR / ".env",
    override=False
)


def get_gemini_api_key():
    """
    Retrieve the Gemini API key from environment variables.

    Supports:
    - Local development using .env
    - Streamlit Community Cloud secrets exposed as
      environment variables
    """

    api_key = (
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "Gemini API key not found. "
            "Please configure GOOGLE_API_KEY in your "
            ".env file or Streamlit Cloud secrets."
        )

    return api_key


# ============================================================
# 3. INITIALIZE GEMINI EMBEDDINGS
# ============================================================

def get_embeddings():
    """
    Initialize Google Gemini embeddings.
    """

    api_key = get_gemini_api_key()

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key
    )

    return embeddings


# ============================================================
# 4. INITIALIZE CHROMADB VECTOR STORE
# ============================================================

def get_vector_store():
    """
    Initialize the ChromaDB vector store using Gemini
    embeddings.

    The vector store contains airline loyalty knowledge
    base documents.
    """

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DIR)
    )

    return vector_store


# ============================================================
# 5. RETRIEVE KNOWLEDGE
# ============================================================

def retrieve_knowledge(query: str, k: int = 3):
    """
    Retrieve relevant airline loyalty knowledge.

    Args:
        query (str): Customer enquiry.
        k (int): Number of relevant documents to retrieve.

    Returns:
        List of LangChain Document objects.
    """

    if not query or not query.strip():
        return []

    if k < 1:
        raise ValueError("k must be greater than zero.")

    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query=query,
        k=k
    )

    return results


# ============================================================
# 6. STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("\n======================================")
    print("AIRLINE LOYALTY KNOWLEDGE RETRIEVAL")
    print("======================================")

    try:

        query = "What should I do if my flight miles are missing?"

        print(f"\nQuery: {query}")

        results = retrieve_knowledge(
            query=query,
            k=3
        )

        print("\n===== RETRIEVED KNOWLEDGE =====\n")

        if not results:
            print(
                "No knowledge documents were retrieved. "
                "Check whether the ChromaDB collection "
                "has been populated."
            )

        for i, document in enumerate(results, start=1):

            print(f"--- Result {i} ---")

            print(
                f"Source: "
                f"{document.metadata.get('source', 'Unknown')}"
            )

            print(document.page_content)

            print()

        print("\nRetrieval test completed.")

    except Exception as error:

        print("\nKnowledge retrieval failed.")

        print(f"Error type: {type(error).__name__}")

        print(f"Error message: {error}")