"""Build the literature review as an editable Word document.

    ./.venv/Scripts/python.exe build_literature_review_docx.py

Reads docs/literature-review.md (the markdown itself is never modified) and
writes docs/literature-review.docx. Headings, bullets, the metadata table in
section 7 and the inline **bold** / *italic* / `code` spans are carried over
so the Word file can be edited and reviewed next to the paper draft.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).parent
SRC = HERE / "docs" / "literature-review.md"
OUT = HERE / "docs" / "literature-review.docx"

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
SEPARATOR_CELL = re.compile(r":?-+:?")


# --------------------------------------------------------------------- inline
def add_inline(par, text: str, *, bold: bool = False, italic: bool = False, mono: bool = False) -> None:
    """Write markdown text into a paragraph, turning spans into runs."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            add_inline(par, part[2:-2], bold=True, italic=italic, mono=mono)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            add_inline(par, part[1:-1], bold=bold, italic=True, mono=mono)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            add_inline(par, part[1:-1], bold=bold, italic=italic, mono=True)
        else:
            run = par.add_run(part)
            run.bold = bold or None
            run.italic = italic or None
            if mono:
                run.font.name = "Courier New"


# -------------------------------------------------------------------- parsing
def parse_blocks(lines: list[str]) -> list[tuple]:
    """Turn markdown lines into ('h', level, text) / ('p', text) / ('li', text)
    / ('hr',) / ('table', raw lines) blocks, joining soft-wrapped lines."""
    blocks: list[tuple] = []
    cur_kind: str | None = None
    cur_lines: list[str] = []

    def flush() -> None:
        nonlocal cur_kind, cur_lines
        if cur_kind is None:
            return
        text = " ".join(x.strip() for x in cur_lines)
        blocks.append((cur_kind, text))
        cur_kind, cur_lines = None, []

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("|"):
            flush()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append(("table", table_lines))
            continue
        if s.startswith("#"):
            flush()
            level = len(s) - len(s.lstrip("#"))
            blocks.append(("h", (level, s.lstrip("#").strip())))
        elif s == "---":
            flush()
            blocks.append(("hr", None))
        elif s == "":
            flush()
        elif s.startswith("- "):
            flush()
            cur_kind, cur_lines = "li", [s[2:]]
        else:
            if cur_kind is None:
                cur_kind, cur_lines = "p", [s]
            else:
                cur_lines.append(s)
        i += 1
    flush()
    return blocks


def table_rows(raw: list[str]) -> list[list[str]]:
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in raw]
    return [r for r in rows if not all(SEPARATOR_CELL.fullmatch(c) for c in r)]


# ---------------------------------------------------------------------- build
def horizontal_rule(doc: Document) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "999999")
    pBdr.append(bottom)
    pPr.insert(0, pBdr)


def make_table(doc: Document, raw: list[str]) -> None:
    rows = table_rows(raw)
    if not rows:
        return
    n_cols = max(len(r) for r in rows)
    widths = [Inches(1.35), Inches(5.15)] if n_cols == 2 else None
    table = doc.add_table(rows=len(rows), cols=n_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    for r, row in enumerate(rows):
        for c in range(n_cols):
            cell = table.cell(r, c)
            text = row[c] if c < len(row) else ""
            par = cell.paragraphs[0]
            par.paragraph_format.space_before = Pt(2)
            par.paragraph_format.space_after = Pt(2)
            add_inline(par, text, bold=(r == 0))
            if widths:
                cell.width = widths[c]
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    title = doc.styles["Title"]
    title.font.name = "Times New Roman"
    title.font.size = Pt(17)
    title.font.bold = True
    title.font.italic = False
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(10)

    h1 = doc.styles["Heading 1"]
    h1.font.name = "Times New Roman"
    h1.font.size = Pt(13)
    h1.font.bold = True
    h1.font.italic = False
    h1.font.color.rgb = RGBColor(0, 0, 0)
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(7)
    h1.paragraph_format.keep_with_next = True

    bullet = doc.styles["List Bullet"]
    bullet.font.name = "Times New Roman"
    bullet.font.size = Pt(11)
    bullet.font.color.rgb = RGBColor(0, 0, 0)
    bullet.paragraph_format.space_after = Pt(3)
    bullet.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def main() -> None:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    blocks = parse_blocks(lines)

    doc = Document()
    configure_styles(doc)

    headings = 0
    table_count = 0
    for kind, payload in blocks:
        if kind == "h":
            level, text = payload
            if level <= 1:
                par = doc.add_paragraph(style="Title")
            else:
                par = doc.add_paragraph(style="Heading 1")
                headings += 1
            add_inline(par, text)
        elif kind == "p":
            par = doc.add_paragraph()
            add_inline(par, payload)
        elif kind == "li":
            par = doc.add_paragraph(style="List Bullet")
            add_inline(par, payload)
        elif kind == "hr":
            horizontal_rule(doc)
        elif kind == "table":
            make_table(doc, payload)
            table_count += 1

    cp = doc.core_properties
    cp.title = "Literature review - MindWeave-R"
    cp.author = "MindWeave-R"
    cp.subject = "Literature review for the IEEE paper draft"

    doc.save(OUT)
    print(f"wrote {OUT} ({headings} sections, {table_count} table)")


if __name__ == "__main__":
    main()
