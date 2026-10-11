import chromadb
from sentence_transformers import SentenceTransformer

TOP_K = 5
lines = open("data/questions.txt", encoding="utf-8-sig").read().splitlines()
questions = [q.strip() for q in lines if q.strip()]

embedder = SentenceTransformer("intfloat/multilingual-e5-small")
col = chromadb.PersistentClient(path="data/chroma").get_collection("sattam_nanban")

for i, q in enumerate(questions, 1):
    vec = embedder.encode("query: " + q, normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=[vec], n_results=TOP_K)
    print("\nQ" + str(i))
    for rank, (doc, meta) in enumerate(zip(res["documents"][0], res["metadatas"][0]), 1):
        print(" ", rank, meta["source"], "|", doc[:70].encode("ascii", "replace").decode())