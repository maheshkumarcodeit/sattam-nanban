"""Sattam Nanban - cut the cleaned documents into chunks and save data/chunks.json.
English page text is cut into overlapping pieces.
The cleaned FAQ is cut so that each question and its answer stay together as one chunk."""
import json
import re
from pathlib import Path

SKIP = {"uyegp_faq.txt", "uyegp_go.txt"}     # garbled FAQ text, and a list of titles with no answers
FAQ_FILE = "uyegp_faq_clean.txt"             # read from page pictures, kept in Tamil and English
CHUNK_SIZE = 400
OVERLAP = 80
MIN_LEN = 100                                # drop tiny leftover chunks

BOILERPLATE = [
    "Contact Us FAQ Follow us on",
    "Micro, Small and Medium Enterprises Department",
    "Unemployed Youth Employment Generation Programme (UYEGP)",
    "Click Here",
    "Screen Reader",
    "Modal title",
]


def clean_page_text(text):
    text = re.sub(r"https?://\S+", " ", text)                                     # web links
    text = re.sub(r"\d{1,2}/\d{1,2}/\d{2},\s*\d{1,2}:\d{2}\s*[AP]M", " ", text)    # print date and time
    text = re.sub(r"\b\d+/\d+\b", " ", text)                                      # page numbers like 1/2
    text = re.sub(r"[^\x00-\x7F]+", " ", text)                                    # these page files are English only
    text = " ".join(text.split())
    for phrase in BOILERPLATE:
        text = text.replace(phrase, " ")
    return " ".join(text.split())


def chunk_page(name, stem, text):
    text = clean_page_text(text)
    out, start, n = [], 0, 0
    while start < len(text):
        piece = text[start:start + CHUNK_SIZE]
        if len(piece) >= MIN_LEN:
            out.append({"id": f"{stem}-{n}", "source": name, "text": piece})
            n += 1
        start += CHUNK_SIZE - OVERLAP
    return out


def chunk_faq(name, stem, text):
    """One chunk per FAQ item (question and answer, in both languages)."""
    out = []
    for block in re.split(r"(?m)^ITEM\s+", text.strip()):
        block = block.strip()
        if not block:
            continue
        number, _, body = block.partition("\n")
        number = re.sub(r"\D", "", number) or str(len(out) + 1)
        body = body.replace("---", " ").strip()
        body = body.replace("Q-TAMIL:", "Question (Tamil):").replace("Q-ENGLISH:", "Question (English):")
        body = body.replace("A-TAMIL:", "Answer (Tamil):").replace("A-ENGLISH:", "Answer (English):")
        body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
        if body:
            out.append({"id": f"{stem}-{number}", "source": name, "text": f"UYEGP FAQ item {number}\n{body}"})
    return out


def main():
    chunks = []
    for f in sorted(Path("data/processed").glob("*.txt")):
        if f.name in SKIP:
            continue
        text = f.read_text(encoding="utf-8")
        if f.name == FAQ_FILE:
            chunks += chunk_faq(f.name, f.stem, text)
        else:
            chunks += chunk_page(f.name, f.stem, text)

    Path("data/chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Total chunks:", len(chunks))
    counts = {}
    for c in chunks:
        counts[c["source"]] = counts.get(c["source"], 0) + 1
    for name, n in counts.items():
        print(" ", name, n)


if __name__ == "__main__":
    main()