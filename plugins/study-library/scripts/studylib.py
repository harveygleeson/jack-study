# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf4llm>=2.1,<2.2"]
# ///
"""studylib: turn textbook PDFs into a searchable Markdown library for Claude.

Run with uv (it installs the dependencies automatically):

    uv run studylib.py inspect  BOOK.pdf
    uv run studylib.py convert  BOOK.pdf --library books [--slug SLUG] [--title T] [--chapter-level N]
    uv run studylib.py check    books/SLUG
    uv run studylib.py figures  books/SLUG [--section NN] [--undescribed] [--limit N]
    uv run studylib.py describe books/SLUG descriptions.json
    uv run studylib.py page     books/SLUG PAGE [--printed] [--dpi 130]
    uv run studylib.py library  books

Layout of a converted book (books/SLUG/):
    _index.md        contents table, section -> file/line map, how page numbers work
    _book-index.md   the book's own back-of-book index (if it has one)
    NN-title.md      one file per chapter, with <!-- page P | printed Q --> markers
    figures/NN/      extracted figure images, referenced from the chapter files
    figures.json     figure manifest (id, page, caption, description)
    book.json        machine-readable metadata
    source.pdf       copy of the original PDF (for viewing pages exactly as printed)
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

try:  # Windows consoles default to a legacy code page
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import pymupdf  # noqa: E402
import pymupdf4llm  # noqa: E402

FORMAT_VERSION = 1
SKIP_TITLES = {"contents", "table of contents", "brief contents", "detailed contents"}
INDEX_TITLES = {"index", "subject index", "general index"}


# ----------------------------------------------------------------- helpers
def slugify(text: str, maxlen: int = 50) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text[:maxlen].rstrip("-")) or "untitled"


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def book_dir_arg(p: str) -> Path:
    d = Path(p).resolve()
    if not (d / "book.json").exists():
        die(f"{d} is not a converted book (no book.json). Pass the folder books/<slug>.")
    return d


# ------------------------------------------------------ PDF introspection
def text_layer_ratio(doc) -> float:
    """Fraction of sampled pages that have a real text layer."""
    n = doc.page_count
    sample = list(range(0, n, max(1, n // 40)))
    good = sum(1 for i in sample if len(doc[i].get_text().strip()) > 200)
    return good / max(1, len(sample))


def detect_page_offset(doc):
    """Find k such that printed page number == pdf page (1-based) - k on most pages."""
    n = doc.page_count
    start = int(n * 0.05)
    sample = list(range(start, n, max(1, (n - start) // 80)))
    counts: collections.Counter = collections.Counter()
    for i in sample:
        lines = [ln.strip() for ln in doc[i].get_text().splitlines() if ln.strip()]
        seen = set()
        for ln in lines[:4] + lines[-4:]:
            for m in re.findall(r"(?<![\d.])(\d{1,4})(?![\d.])", ln):
                off = (i + 1) - int(m)
                if -20 <= off <= 400 and off not in seen:
                    seen.add(off)
                    counts[off] += 1
    if not counts:
        return None
    off, c = counts.most_common(1)[0]
    return off if c >= 0.4 * len(sample) else None


def has_page_labels(doc) -> bool:
    try:
        return any(doc[i].get_label() for i in range(0, doc.page_count, max(1, doc.page_count // 20)))
    except Exception:
        return False


def printed_label(doc, pno0: int, offset):
    """Printed page number (string) for 0-based pdf page, or None."""
    try:
        lab = doc[pno0].get_label()
        if lab:
            return lab
    except Exception:
        pass
    if offset is not None:
        num = pno0 + 1 - offset
        if num >= 1:
            return str(num)
    return None


def suggest_chapter_level(toc) -> int:
    lv = collections.Counter(t[0] for t in toc)
    if lv.get(1, 0) >= 5:
        return 1
    if lv.get(2, 0) >= 5:
        return 2
    return 1


def plan_sections(doc, toc, level: int, pages_per_part: int):
    """Return list of dicts: title, kind (chapter|index|skip|front|part), start, end (0-based, exclusive)."""
    n = doc.page_count
    entries = [(t[1].strip(), t[2] - 1) for t in toc if t[0] <= level and t[2] >= 1]
    entries.sort(key=lambda e: e[1])
    sections = []
    if entries:
        if entries[0][1] > 0:
            entries.insert(0, ("Front matter", 0))
        for idx, (title, start) in enumerate(entries):
            end = entries[idx + 1][1] if idx + 1 < len(entries) else n
            if end <= start:  # e.g. a "Part" heading that shares a page with its first chapter
                continue
            low = title.lower().strip(" .:")
            kind = "skip" if low in SKIP_TITLES else "index" if low in INDEX_TITLES else "chapter"
            sections.append({"title": title, "kind": kind, "start": start, "end": end})
    else:
        for s in range(0, n, pages_per_part):
            e = min(n, s + pages_per_part)
            sections.append({"title": f"Pages {s + 1}-{e}", "kind": "part", "start": s, "end": e})
    return sections


CHAPTER_RE = re.compile(r"^\s*(?:chapter|ch\.?)\s*(\d{1,3})\b[\s:.\-–—]*(.*)$", re.I)
LEADING_NUM_RE = re.compile(r"^\s*(\d{1,3})(?:\s+|\s*[.:]\s+)(?=[A-Za-z])(.*)$")


def assign_file_names(secs) -> None:
    """chNN-title.md for numbered chapters (matching the book), xNN-title.md for everything else."""
    used, other = set(), 0
    for s in secs:
        s["done"] = s["kind"] == "skip"
        if s["kind"] == "skip":
            s["num"], s["file"] = None, None
            continue
        if s["kind"] == "index":
            s["num"], s["file"] = "ix", "_book-index.md"
            continue
        m = CHAPTER_RE.match(s["title"]) or LEADING_NUM_RE.match(s["title"])
        num = f"ch{int(m.group(1)):02d}" if m and s["kind"] == "chapter" else None
        rest = (m.group(2) if m else "") or s["title"]
        if num is None or num in used:
            other += 1
            num, rest = f"x{other:02d}", s["title"]
        used.add(num)
        s["num"] = num
        s["file"] = f"{num}-{slugify(rest)}.md"


# --------------------------------------------------------------- commands
def cmd_inspect(a):
    doc = pymupdf.open(a.pdf)
    toc = doc.get_toc()
    ratio = text_layer_ratio(doc)
    offset = detect_page_offset(doc)
    level = suggest_chapter_level(toc)
    print(f"File: {a.pdf}")
    print(f"Title (metadata): {doc.metadata.get('title') or '(none)'}")
    print(f"Pages: {doc.page_count}")
    print(f"Text layer: {ratio:.0%} of sampled pages have selectable text")
    if ratio < 0.7:
        print("  WARNING: this looks like a scanned/image PDF. Text extraction will be poor;")
        print("  it needs OCR first (e.g. OCRmyPDF) before converting.")
    print(f"Page labels in PDF: {'yes' if has_page_labels(doc) else 'no'}")
    print(f"Printed page offset: {offset if offset is not None else 'not detected'}"
          + (f"  (printed page = pdf page - {offset})" if offset is not None else ""))
    lv = collections.Counter(t[0] for t in toc)
    print(f"Bookmarks (TOC): {len(toc)} entries, per level: {dict(sorted(lv.items()))}")
    print(f"Suggested --chapter-level: {level}")
    if not toc:
        print("  No bookmarks: the book will be split into fixed page ranges.")
    shown = [t for t in toc if t[0] <= max(2, level)][: a.max]
    print("\nTOC (level, title, pdf page):")
    for t in shown:
        print(f"  {'  ' * (t[0] - 1)}[{t[0]}] {t[1]}  — p.{t[2]}")
    if len(shown) < len([t for t in toc if t[0] <= max(2, level)]):
        print(f"  ... (truncated; use --max to see more)")
    print("\nPlanned files at suggested level:")
    secs = plan_sections(doc, toc, level, 30)
    assign_file_names(secs)
    for s in secs:
        print(f"  p.{s['start'] + 1}-{s['end']} ({s['end'] - s['start']}p)  "
              f"{s['file'] or '(skipped: ' + s['title'] + ')'}")


def _md_for_pages(doc, pages, image_dir=None):
    kw = dict(pages=pages, page_chunks=True, show_progress=False)
    if image_dir:
        kw.update(write_images=True, image_path=image_dir, image_format="png", dpi=150)
    for extra in ({"header": False, "footer": False, "use_ocr": False}, {"header": False, "footer": False}, {}):
        try:
            return pymupdf4llm.to_markdown(doc, **kw, **extra)
        except TypeError:
            continue
    return pymupdf4llm.to_markdown(doc, **kw)


IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
CAPTION_RE = re.compile(r"^\W*(fig(?:ure)?\.?|plate|table)\s*[\dA-Z]+[\d.\-–]*", re.I)


def _clean(text: str) -> str:
    text = re.sub(r"</?u>", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _find_caption(lines, i):
    for j in list(range(i + 1, min(len(lines), i + 7))) + list(range(max(0, i - 3), i)):
        s = lines[j].strip()
        if s and CAPTION_RE.match(s):
            return re.sub(r"[*_`]", "", s)[:400].strip()
    return ""


ENDS_WITH_PAGE_RE = re.compile(r"(\d+[a-z]?|[ivxlc]+)[.,;]?\s*$")


def index_page_text(page) -> str:
    """Back-of-book index pages are multi-column; the PDF's native text order follows the columns.
    Re-join entries that wrapped onto a second line ("anterior compartment of the" / "thigh 450")."""
    out, buf = [], ""
    for raw in page.get_text("text").splitlines():
        line = raw.strip()
        if not line:
            continue
        if buf:
            line = f"{buf} {line}"
            buf = ""
        if re.fullmatch(r"[A-Z]", line):  # letter heading
            out.append(f"\n## {line}\n")
        elif ENDS_WITH_PAGE_RE.search(line) or re.search(r"\b[Ss]ee( also)?\b", line):
            out.append(line)
        else:
            buf = line
    if buf:
        out.append(buf)
    return "\n".join(out)


def convert_index_section(doc, book: Path, sec: dict, offset) -> None:
    header = [f"# {sec['title']} (back-of-book index)", "",
              f"<!-- book: {book.name} | file: {sec['file']} | pdf pages {sec['start'] + 1}-{sec['end']} -->", "",
              "Page numbers in this index are PRINTED page numbers (see _index.md for the PDF offset).", ""]
    body, page_lines = list(header), {}
    for p0 in range(sec["start"], sec["end"]):
        printed = printed_label(doc, p0, offset)
        page_lines[p0 + 1] = len(body) + 1
        body += [f"<!-- page {p0 + 1}" + (f" | printed {printed}" if printed else "") + " -->", "",
                 index_page_text(doc[p0]), ""]
    write_text(book / sec["file"], re.sub(r"\n{3,}", "\n\n", "\n".join(body)).rstrip() + "\n")
    sec.update(page_lines=page_lines, figures=0, chars=sum(len(x) for x in body))


def convert_section(doc, book: Path, sec: dict, num: str, offset, figures: list):
    if sec["kind"] == "index":
        return convert_index_section(doc, book, sec, offset)
    fig_rel = f"figures/{num}"
    tmp_rel = f"figures/_tmp{num}"
    cwd = os.getcwd()
    os.chdir(book)  # pymupdf4llm writes image links relative to cwd
    try:
        shutil.rmtree(tmp_rel, ignore_errors=True)
        shutil.rmtree(fig_rel, ignore_errors=True)
        Path(tmp_rel).mkdir(parents=True, exist_ok=True)
        chunks = _md_for_pages(doc, list(range(sec["start"], sec["end"])), tmp_rel)
    finally:
        os.chdir(cwd)
    (book / fig_rel).mkdir(parents=True, exist_ok=True)
    figures[:] = [f for f in figures if f["section"] != num]
    out, page_lines, k = [], {}, 0
    for ch in chunks:
        pno = ch["metadata"]["page_number"]  # 1-based
        printed = printed_label(doc, pno - 1, offset)
        marker = f"<!-- page {pno}" + (f" | printed {printed}" if printed else "") + " -->"
        lines = _clean(ch["text"]).splitlines()
        page_out = [marker, ""]
        for li, line in enumerate(lines):
            m = IMG_RE.search(line)
            if not m:
                page_out.append(line)
                continue
            src = book / m.group(2).replace("\\", "/")
            if not src.exists():
                page_out.append(line)
                continue
            k += 1
            fid = f"{num}-{k:03d}"
            dest_rel = f"{fig_rel}/{fid}.png"
            shutil.move(str(src), str(book / dest_rel))
            caption = _find_caption(lines, li)
            alt = (caption or f"Figure on page {printed or pno}").replace("]", ")").replace("[", "(")
            page_out += [f"<!-- fig {fid} -->", f"![{alt}]({dest_rel})"]
            figures.append({"id": fid, "section": num, "file": sec["file"], "image": dest_rel,
                            "page": pno, "printed": printed, "caption": caption, "description": None})
        out.append((pno, page_out))
    shutil.rmtree(book / tmp_rel, ignore_errors=True)

    header = [f"# {sec['title']}", "",
              f"<!-- book: {book.name} | file: {sec['file']} | pdf pages {sec['start'] + 1}-{sec['end']} -->", ""]
    body, line_no = list(header), len(header)
    for pno, pl in out:
        page_lines[pno] = line_no + 1
        body += pl + [""]
        line_no += len(pl) + 1
    write_text(book / sec["file"], "\n".join(body).rstrip() + "\n")
    sec["page_lines"] = page_lines
    sec["figures"] = k
    sec["chars"] = sum(len(x) for x in body)


def write_book_index(book: Path, meta: dict, toc) -> None:
    off = meta.get("page_offset")
    L = [f"# {meta['title']} — library index", "",
         f"- Slug: `{meta['slug']}` · {meta['pages']} PDF pages · converted {meta['converted']}",
         "- Original PDF: `source.pdf` (view a page exactly as printed with the `page` command)",
         "- Page markers in chapter files look like `<!-- page 1160 | printed 1144 -->`: "
         "the first number is the PDF page, the second is the page number printed in the book. "
         "Cite printed numbers to the student."]
    if off is not None:
        L.append(f"- Printed page = PDF page − {off} (so PDF page = printed + {off}).")
    else:
        L.append("- Printed page numbers could not be detected; cite PDF page numbers.")
    if meta.get("book_index_file"):
        L.append(f"- The book's own back-of-book index is in `{meta['book_index_file']}` "
                 "(it uses PRINTED page numbers) — great for finding every page a term appears on.")
    nfig = meta.get("figure_count", 0)
    L.append(f"- Figures: {nfig} extracted to `figures/`; manifest in `figures.json`. "
             "Each figure is marked `<!-- fig ID -->` in its chapter file.")
    L += ["", "## Files", "", "| # | File | Title | PDF pages | Figures |", "|---|---|---|---|---|"]
    for s in meta["sections"]:
        if s["kind"] in ("skip",):
            continue
        L.append(f"| {s['num']} | `{s['file']}` | {s['title']} | {s['start'] + 1}–{s['end']} | {s.get('figures', 0)} |")
    L += ["", "## Detailed contents", "",
          "Format: title — PDF page (printed page) → file:line. Read the file from that line.", ""]
    secs = [s for s in meta["sections"] if s["kind"] != "skip"]
    for lvl, title, page in toc:
        p0 = page - 1
        sec = next((s for s in secs if s["start"] <= p0 < s["end"]), None)
        if not sec:
            continue
        line = sec.get("page_lines", {}).get(str(page)) or sec.get("page_lines", {}).get(page)
        pr = f" ({page - off})" if off is not None and page - off > 0 else ""
        loc = f"`{sec['file']}`" + (f":{line}" if line else "")
        L.append(f"{'  ' * (lvl - 1)}- {title} — p.{page}{pr} → {loc}")
    write_text(book / "_index.md", "\n".join(L) + "\n")


def cmd_library(a):
    lib = Path(a.library).resolve()
    rows = []
    for bj in sorted(lib.glob("*/book.json")):
        m = read_json(bj)
        figs = read_json(bj.parent / "figures.json", [])
        done = sum(1 for f in figs if f.get("description"))
        rows.append(f"| `{m['slug']}` | {m['title']} | {m['pages']} | {len(figs)} ({done} described) | "
                    f"`{m['slug']}/_index.md` |")
    L = ["# Library", "", "Every book here was converted from PDF. Start with a book's `_index.md`.", "",
         "| Slug | Title | Pages | Figures | Index |", "|---|---|---|---|---|"] + rows
    write_text(lib / "_library.md", "\n".join(L) + "\n")
    print(f"Wrote {lib / '_library.md'} ({len(rows)} books)")


def cmd_convert(a):
    pdf = Path(a.pdf).resolve()
    if not pdf.exists():
        die(f"PDF not found: {pdf}")
    lib = Path(a.library).resolve()
    lib.mkdir(parents=True, exist_ok=True)
    doc0 = pymupdf.open(pdf)
    title = a.title or doc0.metadata.get("title") or pdf.stem
    slug = slugify(a.slug or title, 40)
    book = lib / slug
    meta = read_json(book / "book.json")
    if meta and a.force:
        shutil.rmtree(book)
        meta = None
    if meta is None:
        book.mkdir(parents=True, exist_ok=True)
        dst = book / "source.pdf"
        if not dst.exists():
            print(f"Copying PDF into {dst} ...", flush=True)
            shutil.copy2(pdf, dst)
        doc = pymupdf.open(dst)
        toc = doc.get_toc()
        level = a.chapter_level or suggest_chapter_level(toc)
        secs = plan_sections(doc, toc, level, a.pages_per_part)
        assign_file_names(secs)
        meta = {"format": FORMAT_VERSION, "slug": slug, "title": title, "source_name": pdf.name,
                "pages": doc.page_count, "chapter_level": level, "page_offset": detect_page_offset(doc),
                "converted": _dt.date.today().isoformat(), "sections": secs}
        write_json(book / "book.json", meta)
        print(f"Planned {len(secs)} files for '{title}' -> {book}", flush=True)
    else:
        print(f"Resuming conversion of '{meta['title']}' ({sum(not s['done'] for s in meta['sections'])} files left)")
        doc = pymupdf.open(book / "source.pdf")
        toc = doc.get_toc()

    figures = read_json(book / "figures.json", [])
    todo = [s for s in meta["sections"] if not s["done"]]
    for n, s in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {s['title']} (pdf p.{s['start'] + 1}-{s['end']}) ...", end=" ", flush=True)
        convert_section(doc, book, s, s["num"], meta["page_offset"], figures)
        s["page_lines"] = {str(k): v for k, v in s["page_lines"].items()}
        s["done"] = True
        if s["kind"] == "index":
            meta["book_index_file"] = s["file"]
        write_json(book / "figures.json", figures)
        write_json(book / "book.json", meta)  # checkpoint: safe to interrupt and re-run
        print(f"{s['end'] - s['start']} pages, {s.get('figures', 0)} figures", flush=True)
    meta["figure_count"] = len(figures)
    write_json(book / "book.json", meta)
    write_book_index(book, meta, toc)
    cmd_library(argparse.Namespace(library=str(lib)))
    print(f"\nDONE: {book}\n  {len(figures)} figures, index at {book / '_index.md'}")
    print(f"  Next: uv run studylib.py check \"{book}\"")


def cmd_check(a):
    book = book_dir_arg(a.book)
    meta = read_json(book / "book.json")
    figs = read_json(book / "figures.json", [])
    print(f"{meta['title']} — {meta['pages']} pages, offset {meta.get('page_offset')}")
    pending = [s for s in meta["sections"] if not s["done"]]
    if pending:
        print(f"INCOMPLETE: {len(pending)} files not converted yet — re-run convert to resume.")
    low_pages, weird = [], 0
    for s in meta["sections"]:
        if s["kind"] == "skip" or not s["done"]:
            continue
        text = (book / s["file"]).read_text(encoding="utf-8")
        weird += text.count("�")
        for chunk in re.split(r"<!-- page ", text)[1:]:
            pno = chunk.split(" ", 1)[0].split("-")[0]
            body = re.sub(r"<!--.*?-->|!\[[^\]]*\]\([^)]*\)", "", chunk.split("\n", 1)[-1], flags=re.S)
            if len(body.strip()) < 150 and "<!-- fig" not in chunk:
                low_pages.append(pno)
    print(f"Files: {sum(1 for s in meta['sections'] if s['kind'] != 'skip')} · "
          f"figures: {len(figs)} ({sum(1 for f in figs if f.get('description'))} described, "
          f"{sum(1 for f in figs if f.get('caption'))} with captions)")
    print(f"Near-empty pages (no text, no figure): {len(low_pages)}"
          + (f" e.g. pdf pages {', '.join(low_pages[:15])}" if low_pages else ""))
    print(f"Unreadable characters (\\ufffd): {weird}")
    if len(low_pages) > 0.1 * meta["pages"]:
        print("WARNING: many pages have no text — the PDF may be scanned and need OCR.")
    print("Spot-check: render a page with the `page` command and compare it to the Markdown.")


def cmd_figures(a):
    book = book_dir_arg(a.book)
    figs = read_json(book / "figures.json", [])
    sel = [f for f in figs if (not a.section or f["section"] == a.section)
           and (not a.undescribed or not f.get("description"))]
    print(f"{len(sel)} figures" + (f" (showing {a.limit})" if a.limit and len(sel) > a.limit else ""))
    for f in sel[: a.limit or None]:
        print(f"{f['id']}\tp.{f['page']}" + (f" (printed {f['printed']})" if f.get("printed") else "")
              + f"\t{(book / f['image']).as_posix()}\t{f['file']}\t{f.get('caption') or '(no caption)'}")


def cmd_describe(a):
    book = book_dir_arg(a.book)
    new = json.loads(Path(a.json).read_text(encoding="utf-8"))
    figs = read_json(book / "figures.json", [])
    by_id = {f["id"]: f for f in figs}
    files: dict = collections.defaultdict(list)
    for fid, desc in new.items():
        if fid not in by_id:
            print(f"skip unknown figure id {fid}")
            continue
        desc = " ".join(str(desc).split())
        by_id[fid]["description"] = desc
        files[by_id[fid]["file"]].append((fid, desc))
    for fname, items in files.items():
        p = book / fname
        text = p.read_text(encoding="utf-8")
        for fid, desc in items:
            pat = re.compile(r"(<!-- fig " + re.escape(fid) + r" -->\n!\[[^\n]*\n)"
                             r"(> \*\*Figure description[^\n]*\n(?:>[^\n]*\n)*<!-- /figdesc -->\n)?")
            block = f"> **Figure description ({fid}):** {desc}\n<!-- /figdesc -->\n"
            text, n = pat.subn(lambda m: m.group(1) + block, text, count=1)
            if not n:
                print(f"warning: marker for {fid} not found in {fname}")
        write_text(p, text)
    write_json(book / "figures.json", figs)
    left = sum(1 for f in figs if not f.get("description"))
    print(f"Saved {sum(len(v) for v in files.values())} descriptions. {left} figures still undescribed.")
    cmd_library(argparse.Namespace(library=str(book.parent)))


def cmd_page(a):
    book = book_dir_arg(a.book)
    meta = read_json(book / "book.json")
    page = a.page
    if a.printed:
        if meta.get("page_offset") is None:
            die("printed page numbers were not detected for this book; use the PDF page number")
        page += meta["page_offset"]
    doc = pymupdf.open(book / "source.pdf")
    if not 1 <= page <= doc.page_count:
        die(f"page {page} out of range 1-{doc.page_count}")
    out = book / "_cache" / "pages"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"p{page}.png"
    doc[page - 1].get_pixmap(dpi=a.dpi).save(dest)
    print(dest.as_posix())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inspect", help="show page count, text layer, bookmarks, planned split")
    p.add_argument("pdf"); p.add_argument("--max", type=int, default=120)
    p.set_defaults(fn=cmd_inspect)
    p = sub.add_parser("convert", help="convert a PDF into books/<slug>/ (resumable)")
    p.add_argument("pdf"); p.add_argument("--library", default="books")
    p.add_argument("--slug"); p.add_argument("--title")
    p.add_argument("--chapter-level", type=int, help="TOC level that marks chapters (see inspect)")
    p.add_argument("--pages-per-part", type=int, default=30, help="split size when the PDF has no bookmarks")
    p.add_argument("--force", action="store_true", help="delete any previous conversion and start over")
    p.set_defaults(fn=cmd_convert)
    p = sub.add_parser("check", help="quality report for a converted book")
    p.add_argument("book"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("figures", help="list figures (image path, page, caption)")
    p.add_argument("book"); p.add_argument("--section"); p.add_argument("--undescribed", action="store_true")
    p.add_argument("--limit", type=int, default=0); p.set_defaults(fn=cmd_figures)
    p = sub.add_parser("describe", help="save figure descriptions from a JSON file {id: text}")
    p.add_argument("book"); p.add_argument("json"); p.set_defaults(fn=cmd_describe)
    p = sub.add_parser("page", help="render one page of the original PDF to PNG and print its path")
    p.add_argument("book"); p.add_argument("page", type=int)
    p.add_argument("--printed", action="store_true", help="PAGE is a printed page number")
    p.add_argument("--dpi", type=int, default=130); p.set_defaults(fn=cmd_page)
    p = sub.add_parser("library", help="rebuild books/_library.md")
    p.add_argument("library", nargs="?", default="books"); p.set_defaults(fn=cmd_library)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
