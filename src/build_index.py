import json
import chromadb
from sentence_transformers import SentenceTransformer

chunks = json.load(open("data/chunks.json", encoding="utf-8"))
model = SentenceTransformer("intfloat/multilingual-e5-small")

texts = ["passage: " + c["text"] for c in chunks]
vectors = model.encode(texts, normalize_embeddings=True).tolist()

client = chromadb.PersistentClient(path="data/chroma")
try:
    client.delete_collection("sattam_nanban")
except Exception:
    pass

col = client.create_collection("sattam_nanban", metadata={"hnsw:space": "cosine"})
col.add(
    ids=[c["id"] for c in chunks],
    documents=[c["text"] for c in chunks],
    embeddings=vectors,
    metadatas=[{"source": c["source"]} for c in chunks],
)
print("Stored chunks:", col.count())