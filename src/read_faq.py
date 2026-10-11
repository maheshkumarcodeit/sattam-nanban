"""Read the bilingual UYEGP FAQ by looking at page pictures (the PDF's text layer is garbled)."""
import os
import sys

from rag_final import generate, MODELS, stop   # reuses the safe error handling

PDF = "data/raw/uyegp_faq.pdf"
OUT = "data/processed/uyegp_faq_clean.txt"

PROMPT = """These images are the pages of a bilingual (Tamil and English) FAQ about the UYEGP scheme of the Tamil Nadu government. Each row has a question and an answer, each written in Tamil and in English.

Transcribe every question and answer exactly as shown. Use this format for each item, and number the items in the order they appear:

ITEM <number>
Q-TAMIL: <question in Tamil>
Q-ENGLISH: <question in English>
A-TAMIL: <answer in Tamil>
A-ENGLISH: <answer in English>
---

Rules:
- Do not summarize, shorten, translate, or skip anything.
- Copy all numbers, ages, amounts and percentages exactly as shown.
- If any text is unreadable, write [unclear] in its place.
- Output only the items, with no introduction or closing remarks.
"""


def open_pdf_tool():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        import fitz            # older name of the same tool
        return fitz


def render_pages(path, dpi=150):
    tool = open_pdf_tool()
    doc = tool.open(path)
    pages = [page.get_pixmap(dpi=dpi).tobytes("png") for page in doc]
    doc.close()
    return pages


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        stop("The API key is not set in this window. Run:  set GEMINI_API_KEY=your-key")
    if not os.path.exists(PDF):
        stop(f"{PDF} is missing.")
    try:
        open_pdf_tool()
    except ImportError:
        stop("The picture tool is not installed. Run:  pip install pymupdf")

    from google import genai
    from google.genai import types

    pages = render_pages(PDF)
    print("Pages turned into pictures:", len(pages))
    parts = [types.Part.from_bytes(data=p, mime_type="image/png") for p in pages]

    client = genai.Client()
    state = {"i": 0}
    text, model = generate(client, parts + [PROMPT], state, MODELS)
    if text is None:
        stop("All models are out of quota or failing right now. Try again later.")

    os.makedirs("data/processed", exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    items = text.count("ITEM ")
    print(f"Done. Model: {model}. Items found: {items}. Characters: {len(text)}")
    print(f"Open {OUT} in Notepad and compare it with the PDF.")


if __name__ == "__main__":
    main()