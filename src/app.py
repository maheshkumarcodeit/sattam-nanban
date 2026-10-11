"""Sattam Nanban - web demo.
Run from the project folder with:  python -m streamlit run src\\app.py"""
import os
import sys
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rag_final as R   # reuses the tested retrieval, prompt and error handling

SOURCE_LABELS = {
    "udyam_tn.txt": "Tamil Nadu MSME Dept: Udyam Registration page (saved 2 Oct 2026)",
    "uyegp_about.txt": "Tamil Nadu MSME Dept: UYEGP scheme overview page (saved 2 Oct 2026)",
    "uyegp_procedure.txt": "Tamil Nadu MSME Dept: UYEGP application procedure page (saved 2 Oct 2026)",
    "uyegp_faq_clean.txt": "Tamil Nadu MSME Dept: UYEGP FAQ (no date shown on the page)",
}
EXAMPLES = [
    "உத்யம் பதிவுக்கு கட்டணம் உண்டா?",
    "UYEGP திட்டத்தில் சேர வயது வரம்பு என்ன?",
    "UYEGP திட்டத்தில் குடும்ப வருமான வரம்பு எவ்வளவு?",
]
MAX_PER_SESSION = 10      # protects the free Gemini allowance
MAX_QUESTION_LENGTH = 300

st.set_page_config(page_title="Sattam Nanban", page_icon="⚖️", layout="centered")


@st.cache_resource(show_spinner="Loading the search model, please wait...")
def load_tools():
    import chromadb
    from sentence_transformers import SentenceTransformer
    from google import genai
    col = chromadb.PersistentClient(path="data/chroma").get_collection("sattam_nanban")
    embedder = SentenceTransformer("intfloat/multilingual-e5-small")
    client = genai.Client()
    return col, embedder, client, {"i": 0}


def label(name):
    return SOURCE_LABELS.get(name, name)


def parse_sources(used):
    names = [n.strip() for n in used.replace(";", ",").split(",")]
    return [n for n in names if n and n.lower() != "none"]


def answer_question(question):
    col, embedder, client, state = load_tools()
    vec = embedder.encode("query: " + question, normalize_embeddings=True).tolist()
    found = R.retrieve(col, vec)
    context = "".join(f"[Source: {src}]\n{doc}\n\n" for doc, src in found)
    text, _model = R.generate(client, R.build_prompt(question, context), state, R.MODELS,
                              sleep=lambda s: time.sleep(3))
    return text, found


def set_question(text):
    st.session_state.q = text


# ---------------- page ----------------
st.title("சட்டம் நண்பன் · Sattam Nanban")
st.caption("Ask in Tamil. Get answers from official Tamil Nadu MSME pages.")
st.warning(
    "Prototype. Answers come only from a small set of saved official pages. "
    "These pages may be out of date or disagree with each other. "
    "Always confirm with your District Industries Centre (DIC) before acting."
)

with st.sidebar:
    st.header("How it works")
    st.write("1. Your question is matched against saved official pages.")
    st.write("2. The best matching passages are given to an AI model.")
    st.write("3. The model answers only from those passages, or says it could not find the answer.")
    st.header("Documents used")
    for name in SOURCE_LABELS:
        st.write("• " + label(name))
    st.caption("Built by Maheshkumar S · RAG with Gemini and ChromaDB · Not legal or financial advice.")

if not os.path.isdir("data/chroma"):
    st.error("The saved index was not found. Start this app from the sattam-nanban project folder.")
    st.stop()
if not os.environ.get("GEMINI_API_KEY"):
    st.error("The API key is not set in this window. Close the app, run:  set GEMINI_API_KEY=your-key  "
             "then start it again.")
    st.stop()

if "q" not in st.session_state:
    st.session_state.q = ""
if "count" not in st.session_state:
    st.session_state.count = 0

st.write("**Try an example:**")
for ex in EXAMPLES:
    st.button(ex, on_click=set_question, args=(ex,), key="ex_" + ex)

st.text_area("Your question / உங்கள் கேள்வி", key="q", height=100,
             placeholder="உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யுங்கள்")

if st.button("Ask / கேளுங்கள்", type="primary"):
    question = st.session_state.q.strip()
    if not question:
        st.info("Please type a question first.")
    elif len(question) > MAX_QUESTION_LENGTH:
        st.info(f"Please keep the question under {MAX_QUESTION_LENGTH} characters.")
    elif st.session_state.count >= MAX_PER_SESSION:
        st.info("This demo is limited to %d questions per visit. Please come back later." % MAX_PER_SESSION)
    else:
        try:
            with st.spinner("Searching the documents..."):
                text, found = answer_question(question)
        except SystemExit:
            st.error("Google rejected the API key. Please check it and restart the app.")
        except Exception as e:
            st.error("Something went wrong: " + str(e)[:150])
        else:
            if text is None:
                st.info("The AI service is busy, or its free allowance is used up for now. "
                        "Please try again in a few minutes.")
            else:
                st.session_state.count += 1
                answer, used = R.split_used(text)
                st.subheader("Answer / பதில்")
                st.info(answer.replace("*", "\\*"))
                names = parse_sources(used)
                if names:
                    st.write("**Sources used:**")
                    for n in names:
                        st.write("• " + label(n))
                else:
                    st.caption("No document was used for this answer.")
                with st.expander("Show the text this answer was based on"):
                    for doc, src in found:
                        st.markdown("**" + label(src) + "**")
                        st.text(doc[:900])