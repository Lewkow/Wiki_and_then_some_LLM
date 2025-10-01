# ingest/wiki_stream.py
from __future__ import annotations
import bz2
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator, Tuple, Optional

def _lname(tag: str) -> str:
    return tag.split('}', 1)[-1] if '}' in tag else tag

def _find_local(parent: ET.Element, name: str) -> Optional[ET.Element]:
    for child in parent:
        if _lname(child.tag) == name:
            return child
    return None

def _iter_pages_from_fileobj(fileobj) -> Iterator[Tuple[str, str]]:
    context = ET.iterparse(fileobj, events=("end",))
    for _, elem in context:
        if _lname(elem.tag) == "page":
            title_el = _find_local(elem, "title")
            rev_el = _find_local(elem, "revision")
            text_el = _find_local(rev_el, "text") if rev_el is not None else None
            title = (title_el.text or "").strip() if title_el is not None else ""
            text = (text_el.text or "").strip() if text_el is not None and text_el.text else ""
            if title and text:
                yield title, text
            elem.clear()  # keep memory flat

def iter_pages(xml_or_bz2_path: Path) -> Iterator[Tuple[str, str]]:
    p = Path(xml_or_bz2_path)
    if p.suffix == ".bz2":
        with bz2.open(str(p), "rb") as fh:
            yield from _iter_pages_from_fileobj(fh)
    else:
        with open(str(p), "rb") as fh:
            yield from _iter_pages_from_fileobj(fh)

def guess_wiki_base(path_str: str) -> str:
    return "https://simple.wikipedia.org/wiki/" if "simplewiki" in path_str else "https://en.wikipedia.org/wiki/"
