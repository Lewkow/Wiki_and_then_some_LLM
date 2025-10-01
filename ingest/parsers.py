from pathlib import Path
from pypdf import PdfReader
from docx import Document

def read_txt_md(path: Path) -> str:
    return path.read_text(errors="ignore")

def read_pdf(path: Path) -> str:
    out = []
    reader = PdfReader(str(path))
    for page in reader.pages:
        out.append(page.extract_text() or "")
    return "\n".join(out)

def read_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)

def load_any(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in [".txt", ".md"]:
        return read_txt_md(path)
    if ext == ".pdf":
        return read_pdf(path)
    if ext in [".docx"]:
        return read_docx(path)
    return ""

