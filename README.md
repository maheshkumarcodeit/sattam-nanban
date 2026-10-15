# Sattam Nanban (சட்டம் நண்பன்)

A Tamil-first assistant that answers small business owners' questions about Tamil Nadu government registration and schemes. Answers come only from saved official pages. If the pages don't contain the answer, it says so and points to the nearest District Industries Centre (DIC) instead of guessing.

**Status:** working prototype that runs on a laptop. Not a public service, and not legal or financial advice.

## The problem

Rules like Udyam registration and the UYEGP loan-subsidy scheme are explained mostly in English, across many web pages that don't always agree. A general chatbot may answer confidently from memory and be wrong. This project asks a narrower question: can an AI answer in Tamil, from official text only, and be honest when it can't?

## How it works

**Preparing the documents (done once)**

1. Official pages are saved as PDFs.
2. Text is extracted and cleaned (links, timestamps, page footers and menu text removed).
3. One FAQ has Tamil text in an old font encoding that extracts as gibberish. Its pages are turned into pictures and read by Gemini, giving clean Tamil and English question-and-answer pairs.
4. Page text is cut into chunks of about 400 characters. Each FAQ item stays together as one chunk.
5. A multilingual embedding model turns every chunk into a vector, and the vectors are stored in ChromaDB. This lets a Tamil question match English text by meaning.

**Answering a question**

1. The Tamil question is embedded the same way.
2. The best 3 chunks from the FAQ and the best 4 chunks from all other pages are retrieved separately, so no one source can crowd out the others.
3. The chunks go to Gemini with strict instructions: answer only from this context, in Tamil script; say what is missing if the context covers only part of the question; if sources give different figures, give each one and name its source; if the answer isn't there, say so.
4. The page shows the answer, the sources used, and the passages the answer was based on.

## Tech stack

| Part | Choice |
|---|---|
| Language | Python 3.12 |
| PDF reading | pypdf, PyMuPDF (page pictures) |
| Embeddings | intfloat/multilingual-e5-small (sentence-transformers) |
| Vector database | ChromaDB (local) |
| LLM | Google Gemini, free tier, with fallback between models |
| Web demo | Streamlit |

Built from scratch, with no LangChain or LlamaIndex.

## Repository contents

| File | Purpose |
|---|---|
| `src/read_all.py` | Extract text from the saved PDFs |
| `src/read_faq.py` | Read the FAQ pages as pictures with Gemini |
| `src/chunk.py` | Clean the text and cut it into chunks |
| `src/build_index.py` | Embed the chunks and store them in ChromaDB |
| `src/retrieval_check.py` | Show which chunks come back per question (no Gemini needed) |
| `src/rag_final.py` | Retrieval, prompt and Gemini calls, plus a 10-question batch runner |
| `src/app.py` | Streamlit web demo |
| `data/questions.txt` | The 10 Tamil test questions |

## Data sources

Saved on 2 October 2026 from the Tamil Nadu MSME Department site (msmeonline.tn.gov.in):

- Udyam Registration page (`udyam_regis.php`)
- UYEGP scheme overview page (`uyegp/uyegp_desc.php`)
- UYEGP application procedure page
- UYEGP FAQ page (bilingual)
- UYEGP government orders page (`uyegp/uyegp_go.php`): saved but not indexed, because it is only a list of order titles

The saved pages and the search index are **not** in this repository, because they are copies of government pages. To rebuild, save the pages yourself as PDFs (Ctrl+P, then Save as PDF) into `data/raw/`.

## Evaluation

I tested with 10 Tamil questions, including one deliberate trap (GST, which has no source document). I scored the answers by hand against the saved pages. Each row is a single run of the same 10 questions.

| Round | What changed | Result |
|---|---|---|
| 1 | First working version, 3 chunks per question | 5 clear passes, 1 fail, 1 partial, 3 faithful but misleading |
| 2 | 5 chunks, list-of-titles page removed from the index | 5 clear passes, 1 pass with a stray foreign word, 2 partial, 2 conflicts hidden, 0 fails |
| 3 | Prompt: no greeting, Tamil script only, list the sources used | 6 clear passes, 0 fails, 2 partial, 2 conflicts hidden |
| 4 | Prompt: say what is missing when the answer is only partial | 6 clear passes, 2 honest partials, 2 conflicts hidden, 0 fails |
| 5 | FAQ added to the index, plain top-5 retrieval | **Worse:** 2 clear passes, 1 partial, 3 conflicts hidden, **4 wrong "not in the documents"** answers |
| 6 | Balanced retrieval (FAQ and other pages searched separately) | Built and tested on a stand-in index. **Results of a full 10-question run not yet reviewed** |

Caveats: hand-scored by the author, 10 questions only, the same questions were used for tuning, and each result is one sample. Treat these numbers as development notes, not proof of quality.

## Findings

1. **Official pages disagree.** The UYEGP overview page and the FAQ give different figures: upper age (45 vs 35 for general, 55 vs 45 for special categories), family income (below Rs 8 lakh vs not above Rs 1.5 lakh) and maximum subsidy (up to Rs 3.75 lakh vs Rs 1,25,000). Neither saved page shows a date, so I can't tell which is current. The FAQ may be older, but that is unconfirmed. The app should flag the difference and show sources, not pick one.
2. **Adding a source can hurt the others.** In round 5 the Tamil FAQ chunks matched Tamil questions so strongly that English page chunks were pushed out, even for unrelated Udyam questions. My explanation is a language bias in the embedding model. The retrieval lists fit it, but I haven't proven it.
3. **True is not the same as current.** An answer can match its document and still be outdated or incomplete.
4. **Honest "not found" held up.** The GST trap question was answered with "not found" in every round and in the web demo.
5. **Old government PDFs can hide garbled Tamil.** A page can look perfect on screen while its text layer is unreadable by code.
6. **Free-tier limits shape the product.** One model allowed only 20 requests per day, and failed attempts seemed to count toward the limit.

## Known limitations and roadmap

- [ ] Review a full 10-question run with balanced retrieval and update the table above
- [ ] Confirm the app names both figures when pages disagree
- [ ] Show each document's date next to its answers
- [ ] Add a GST source document
- [ ] A fresh set of unseen test questions
- [ ] Public demo, which needs a plan for the free-tier request limit

## Run it yourself (Windows)

1. Clone the repository. In the project folder, run `python -m venv venv`, then `venv\Scripts\activate`, then `pip install -r requirements.txt`.
2. Save the source pages as PDFs into `data/raw/`, named `udyam_tn.pdf`, `uyegp_about.pdf`, `uyegp_faq.pdf` and `uyegp_procedure.pdf`.
3. Get a free Gemini API key from Google AI Studio and set it for the window with `set GEMINI_API_KEY=your-key`. Never put the key in a file.
4. Build the index by running these four commands in order: `python src\read_all.py`, then `python src\read_faq.py`, then `python src\chunk.py`, then `python src\build_index.py`.
5. Start the demo with `python -m streamlit run src\app.py`.

Gemini model names change over time. If a model is unavailable, edit the `MODELS` list at the top of `src/rag_final.py`.

## How this was built

I built this with an AI assistant guiding me step by step, and I'm learning the code as I go. My own work is the problem choice, collecting and cleaning the sources, designing the test questions, scoring the answers, and deciding what to fix next. The findings above come from reading results and tracing each problem back to a pipeline step.

## Disclaimer

Answers are drawn from saved copies of official pages, which may be out of date or contradict each other. Always confirm with your District Industries Centre before acting. This is a learning project, not legal or financial advice.

Author: Maheshkumar S