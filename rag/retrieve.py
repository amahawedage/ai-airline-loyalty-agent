from pathlib import Path
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DIR = BASE_DIR / "chroma_db"


def get_vector_store():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    return Chroma(
        collection_name="airline_loyalty_kb",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DIR)
    )


def retrieve_knowledge(query: str, k: int = 3):
    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query,
        k=k
    )

    return results


if __name__ == "__main__":
    query = "What should I do if my flight miles are missing?"

    results = retrieve_knowledge(query)

    print("\n===== RETRIEVED KNOWLEDGE =====\n")

    for i, document in enumerate(results, start=1):
        print(f"--- Result {i} ---")
        print(f"Source: {document.metadata.get('source')}")
        print(document.page_content)
        print()