
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001"
)

CHROMA_DIR = ROOT_DIR / os.getenv(
    "CHROMA_PERSIST_DIRECTORY",
    "./chroma_db"
)

COLLECTION_NAME = os.getenv(
    "CHROMA_COLLECTION",
    "hr_it_policies"
)

TOP_K = int(os.getenv("RAG_TOP_K", "5"))

if not API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")


# --------------------------------------------------
# CLIENT INITIALIZATION
# --------------------------------------------------

gemini_client = genai.Client(
    api_key=API_KEY
)

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# RAG RETRIEVAL
# --------------------------------------------------

def retrieve_policy_context(
    question: str,
    top_k: int = TOP_K
):
    """
    Retrieve relevant HR and IT policy chunks.

    Returns:
        List of dictionaries containing:
        - text
        - filename
        - section
        - chunk_id
        - distance
    """

    if not question or not question.strip():
        return []

    if top_k < 1:
        return []

    if collection.count() == 0:
        return []

    # Generate query embedding using Gemini
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config={
            "task_type": "RETRIEVAL_QUERY"
        }
    )

    if not response.embeddings:
        return []

    query_embedding = response.embeddings[0].values

    # Retrieve relevant chunks from ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where={"type": "policy"},
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    retrieved = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        retrieved.append({
            "text": document,
            "filename": metadata["filename"],
            "section": metadata["section"],
            "chunk_id": metadata["chunk_id"],
            "distance": distance
        })

    return retrieved


# --------------------------------------------------
# SOURCE FORMATTING
# --------------------------------------------------

def format_sources(results):
    """
    Generate unique source references.
    """

    sources = []

    for result in results:

        source = (
            result["filename"],
            result["section"]
        )

        if source not in sources:
            sources.append(source)

    return [
        {
            "filename": filename,
            "section": section
        }
        for filename, section in sources
    ]


# --------------------------------------------------
# CLI TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("HR & IT Policy Retrieval")
    print("------------------------")

    question = input("\nAsk a policy question: ")

    try:

        results = retrieve_policy_context(question)

        if not results:

            print("\nNo policy documents found.")

        else:

            for index, result in enumerate(results, 1):

                print(f"\n--- RESULT {index} ---")

                print("File:", result["filename"])
                print("Section:", result["section"])
                print("Distance:", round(result["distance"], 4))
                print("\nContent:")
                print(result["text"])

            print("\n--- SOURCES ---")

            for source in format_sources(results):

                print(
                    f"- {source['filename']} "
                    f"| {source['section']}"
                )

    except Exception as error:

        print("\nRetrieval failed:", str(error))
