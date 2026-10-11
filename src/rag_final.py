"""Sattam Nanban - final batch runner.
Reads data/questions.txt, retrieves chunks from Chroma, asks Gemini, saves answers.
Edit only the SETTINGS block below."""
import os
import sys
import time
import logging

os.environ.setdefault("HF_HUB_OFFLINE", "1")        # embedding model is already downloaded
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
logging.getLogger("google_genai").setLevel(logging.ERROR)

# ======================= SETTINGS =======================
MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
FAQ_FILE = "uyegp_faq_clean.txt"
N_FAQ = 3                         # best chunks taken from the FAQ
N_PAGES = 4                       # best chunks taken from all the other pages
ONLY = []                         # [] = all questions. Or e.g. [4, 7] for just those.
OUTFILE = "data/answers_final.txt"
PAUSE_BETWEEN = 8                 # seconds between questions
# ========================================================


def stop(message):
    print("\nSTOP:", message)
    sys.exit(1)


def classify(msg):
    """Turn a Google error message into a simple kind."""
    up = msg.upper()
    if "PERDAY" in up or "PER_DAY" in up:
        return "day"
    if "429" in msg or "RESOURCE_EXHAUSTED" in up:
        return "minute"
    if "API_KEY" in up or "API KEY" in up or "PERMISSION_DENIED" in up or "UNAUTHENTICATED" in up:
        return "key"
    if "404" in msg or "NOT_FOUND" in up:
        return "missing"
    if "503" in msg or "UNAVAILABLE" in up or "500" in msg or "INTERNAL" in up or "DEADLINE" in up:
        return "busy"
    return "other"


def split_used(text):
    """Separate the final 'USED: ...' line from the answer."""
    lines = text.strip().splitlines()
    used = ""
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().upper().startswith("USED:"):
            used = lines[i].split(":", 1)[1].strip()
            lines = lines[:i]
            break
    return "\n".join(lines).strip(), used


def build_prompt(question, context):
    return f"""You are Sattam Nanban, an assistant that helps small business owners in Tamil Nadu understand government schemes and registration rules.

Answer the question using ONLY the context below.
- Start directly with the answer. Do not greet the user and do not introduce yourself.
- Reply in the same language as the question. For Tamil questions, write only in Tamil script. Names like UYEGP, Udyam, Aadhaar, PAN, DIC and numbers may stay as they are. Do not use words from any other language.
- If the context does not contain the answer, say you could not find it in the documents and suggest contacting the nearest District Industries Centre (DIC).
- If the context answers only part of the question, give that part and clearly say what is missing, then suggest contacting the nearest District Industries Centre (DIC) for the rest.
- If different sources give different figures for the same thing, say the documents differ, give each figure, and name the source file for each. Do not choose between them.
- In Tamil text, write District Industries Centre as மாவட்ட தொழில் மையம் (DIC).
- Keep the answer short and simple. Do not invent numbers or rules.
- On the very last line, write USED: followed by the file names of the sources you actually used. If you used none, write USED: none.

Context:
{context}
Question: {question}
"""


def retrieve(col, vec, faq_file=FAQ_FILE, n_faq=N_FAQ, n_pages=N_PAGES):
    """Take the best chunks from the FAQ and from the other pages separately,
    so that one source cannot crowd the others out."""
    found = []
    for where, n in (({"source": faq_file}, n_faq), ({"source": {"$ne": faq_file}}, n_pages)):
        res = col.query(query_embeddings=[vec], n_results=n, where=where)
        for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
            found.append((doc, meta["source"]))
    return found


def generate(client, prompt, state, models, sleep=time.sleep):
    """Try the current model; on daily limit or missing model, move to the next one."""
    while state["i"] < len(models):
        model = models[state["i"]]
        moved_on = False
        for attempt in range(4):
            try:
                r = client.models.generate_content(model=model, contents=prompt)
                text = (r.text or "").strip()
                if text:
                    return text, model
                print("  empty answer, trying again...")
                sleep(5)
            except SystemExit:
                raise
            except Exception as e:
                msg = str(e)
                kind = classify(msg)
                if kind == "key":
                    stop("Google rejected the API key. Create a new key at aistudio.google.com/apikey, "
                         "then run:  set GEMINI_API_KEY=your-key")
                if kind in ("day", "missing"):
                    why = "daily limit reached" if kind == "day" else "not available"
                    print(f"  {model}: {why}. Trying the next model.")
                    moved_on = True
                    break
                if kind == "minute":
                    print("  per-minute limit, waiting 65 seconds...")
                    sleep(65)
                elif kind == "busy":
                    print("  Gemini is busy, waiting 20 seconds...")
                    sleep(20)
                else:
                    print("  unexpected error:", msg[:120].encode("ascii", "replace").decode())
                    sleep(10)
        if not moved_on:
            print(f"  {model} kept failing. Trying the next model.")
        state["i"] += 1
    return None, None


def main():
    # ---- checks before doing any work ----
    if not os.environ.get("GEMINI_API_KEY"):
        stop("The API key is not set in this window. Run:  set GEMINI_API_KEY=your-key   "
             "then run this script again.")
    if not os.path.exists("data/questions.txt"):
        stop("data\\questions.txt is missing.")
    if not os.path.isdir("data/chroma"):
        stop("data\\chroma is missing. Run:  python src\\build_index.py")

    import chromadb
    from sentence_transformers import SentenceTransformer
    from google import genai

    try:
        col = chromadb.PersistentClient(path="data/chroma").get_collection("sattam_nanban")
    except Exception:
        stop("Could not open the saved index. Run:  python src\\build_index.py")
    if col.count() == 0:
        stop("The index is empty. Run:  python src\\build_index.py")

    lines = open("data/questions.txt", encoding="utf-8-sig").read().splitlines()
    questions = [q.strip() for q in lines if q.strip()]
    selected = [(i, q) for i, q in enumerate(questions, 1) if not ONLY or i in ONLY]
    if not selected:
        stop("No questions selected. Check the ONLY setting.")

    embedder = SentenceTransformer("intfloat/multilingual-e5-small")
    client = genai.Client()
    state = {"i": 0}

    mode = "a" if ONLY else "w"          # a specific list adds to the file, a full run starts fresh
    with open(OUTFILE, mode, encoding="utf-8") as f:
        f.write(f"##### RUN {time.strftime('%Y-%m-%d %H:%M')} #####\n\n")

    done = 0
    for pos, (i, q) in enumerate(selected):
        print(f"Question {i} of {len(questions)}")
        vec = embedder.encode("query: " + q, normalize_embeddings=True).tolist()
        context, retrieved = "", []
        for doc, source in retrieve(col, vec):
            context += f"[Source: {source}]\n{doc}\n\n"
            retrieved.append(source)

        text, model = generate(client, build_prompt(q, context), state, MODELS)
        if text is None:
            remaining = [n for n, _ in selected[pos:]]
            print(f"\nAll models are out of quota or failing. {done} answers are saved.")
            print("To finish later, set this in the SETTINGS block:  ONLY =", remaining)
            break

        answer, used = split_used(text)
        block = (f"#{i} QUESTION: {q}\nANSWER:\n{answer}\n"
                 f"SOURCES USED: {used or '(not reported)'}\n"
                 f"RETRIEVED: {', '.join(sorted(set(retrieved)))}\n"
                 f"MODEL: {model}\n\n{'=' * 60}\n\n")
        with open(OUTFILE, "a", encoding="utf-8") as f:
            f.write(block)
        done += 1
        time.sleep(PAUSE_BETWEEN)

    print(f"\nFinished. {done} answers saved in {OUTFILE}")


if __name__ == "__main__":
    main()