"""Policy ingestion module."""

import os
import re
import hashlib
from pathlib import Path

import chromadb
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from google import genai


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT_DIR / "data" / "policies"

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

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

if not API_KEY:
    raise ValueError("Set GEMINI_API_KEY in .env")

client = genai.Client(api_key=API_KEY)

encoding = tiktoken.get_encoding("cl100k_base")

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# TEXT PROCESSING
# --------------------------------------------------

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
):
    tokens = encoding.encode(text)

    if not tokens:
        return []

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size")

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))

        chunk_tokens = tokens[start:end]

        chunks.append(
            encoding.decode(chunk_tokens)
        )

        if end == len(tokens):
            break

        start = end - overlap

    return chunks


def extract_sections(text: str):
    """
    Split a Markdown document by headings.
    Each section retains its heading.
    """

    sections = []
    current_heading = "Introduction"
    current_content = []

    for line in text.splitlines():

        heading_match = re.match(
            r"^(#{1,6})\s+(.+)$",
            line.strip()
        )

        if heading_match:

            if current_content:
                content = "\n".join(current_content).strip()

                if content:
                    sections.append({
                        "heading": current_heading,
                        "content": content
                    })

            current_heading = heading_match.group(2).strip()
            current_content = []

        else:
            current_content.append(line)

    if current_content:
        content = "\n".join(current_content).strip()

        if content:
            sections.append({
                "heading": current_heading,
                "content": content
            })

    return sections


def create_chunk_id(filename, section, index, content):
    raw = f"{filename}:{section}:{index}:{content}"

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# --------------------------------------------------
# DOCUMENT INGESTION
# --------------------------------------------------

def load_policy_documents():

    if not POLICY_DIR.exists():
        raise FileNotFoundError(
            f"Policy directory not found: {POLICY_DIR}"
        )

    documents = []

    for file_path in sorted(POLICY_DIR.glob("*.md")):

        text = file_path.read_text(
            encoding="utf-8"
        )

        sections = extract_sections(text)

        for section in sections:

            chunks = split_into_chunks(
                section["content"]
            )

            for index, chunk in enumerate(chunks):

                documents.append({
                    "id": create_chunk_id(
                        file_path.name,
                        section["heading"],
                        index,
                        chunk
                    ),
                    "text": chunk,
                    "metadata": {
                        "filename": file_path.name,
                        "section": section["heading"],
                        "chunk_id": index
                    }
                })

    return documents


# --------------------------------------------------
# EMBEDDINGS
# --------------------------------------------------

def generate_embeddings(texts):

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config={
            "task_type": "RETRIEVAL_DOCUMENT"
        }
    )

    return [
        item.values
        for item in response.embeddings
    ]

# --------------------------------------------------
# CHROMADB STORAGE
# --------------------------------------------------

def ingest_documents():

    documents = load_policy_documents()

    if not documents:
        raise ValueError("No policy documents found")

    print(f"Loaded {len(documents)} chunks.")

    # Remove existing collection entries to prevent
    # stale chunks when policy documents are updated.

    collection.delete(where={"type": "policy"})

    batch_size = 50

    for start in range(0, len(documents), batch_size):

        batch = documents[start:start + batch_size]

        texts = [
            item["text"]
            for item in batch
        ]

        embeddings = generate_embeddings(texts)

        collection.upsert(
            ids=[
                item["id"]
                for item in batch
            ],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                {
                    **item["metadata"],
                    "type": "policy"
                }
                for item in batch
            ]
        )

        print(
            f"Ingested {min(start + batch_size, len(documents))}"
            f"/{len(documents)} chunks."
        )

    print("\nIngestion completed successfully.")
    print("Total stored chunks:", collection.count())


if __name__ == "__main__":
    ingest_documents()
