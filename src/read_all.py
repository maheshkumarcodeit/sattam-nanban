from pathlib import Path
from pypdf import PdfReader

raw = Path("data/raw")
out = Path("data/processed")

for pdf in sorted(raw.glob("*.pdf")):
    reader = PdfReader(pdf)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    (out / (pdf.stem + ".txt")).write_text(text, encoding="utf-8")
    print(f"{pdf.name}: {len(reader.pages)} pages, {len(text)} characters")