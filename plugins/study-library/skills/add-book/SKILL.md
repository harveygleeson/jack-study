---
name: add-book
description: Convert a textbook PDF into the study library (searchable Markdown split by chapter, extracted figures, page references, back-of-book index). Use when the user wants to add, import or convert a book or PDF, or re-convert one that came out badly.
---

# Add a book to the library

The tool is `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/studylib.py"`, shortened to **studylib** below. Run commands from the workspace folder (the one with `books/`). If `books/` doesn't exist, run the `study-setup` skill first. If `uv` isn't found, see that skill's uv step.

## 1. Find the PDF
Use the path the student gave you. If they only gave a name, look in common places (Downloads, Desktop, Documents, this folder). Confirm the file before converting. Large medical textbooks are often 300 MB to 1 GB, and that's fine.

## 2. Inspect it
`studylib inspect "<pdf>"`

Read the report:
- **Text layer below ~70%** means it's a scanned book. Stop and explain: the pages are pictures of text, so they need OCR first. Offer to look into OCR (for example OCRmyPDF), and warn that it's slow and less accurate. Don't convert a scanned book without the student agreeing.
- **Chapter split.** Check "Planned files". The goal is roughly one file per chapter (about 10–80 pages each).
  - If most planned files are "Part I/II…" with hundreds of pages, use `--chapter-level 2`.
  - If there are hundreds of tiny files, use a lower level.
  - With no bookmarks it splits every 30 pages. That works, but tell the student.
- **Printed page offset.** Note whether it was detected. Without it, citations use PDF page numbers.

## 3. Convert
`studylib convert "<pdf>" --library books --slug <short-slug> --title "<Proper Title, Edition>"`

- Choose a short memorable slug, e.g. `guyton-14e`, `robbins-basic-path-11e`, `harrison-21e`.
- A 1,500-page book takes roughly 5–20 minutes. **Run it in the background** if you can, and tell the student it's working. Conversion is **resumable**: if it stops or times out, run the same command again and it carries on from the last finished chapter. Use `--force` only to start over (for example with a different `--chapter-level`).

## 4. Check the quality. Don't skip this.
1. `studylib check books/<slug>` reports near-empty pages and broken characters.
2. Open `books/<slug>/_index.md` and check that chapter titles and page numbers look right.
3. Spot-check two places, one text-heavy and one with a table or diagram:
   - render the original with `studylib page books/<slug> <pdf-page>` and view the PNG it prints;
   - read the same page in the chapter `.md` (search for `<!-- page N`);
   - compare. Are the words in the right order? Are tables readable? Are figures linked?
4. View one or two extracted figures, using the path from `studylib figures books/<slug> --limit 5`, to confirm the labels are intact.

Tell the student what you found, honestly: what came out well and anything to be aware of (for example "tables in chapter 12 lost some formatting, so I'll check the original page when we use them").

## 5. Figures
Most textbook figures have captions, which are already searchable. Written descriptions make the **contents** of a diagram searchable too, but they take a lot of usage: one image view per figure, and a big book can have 1,000+ figures.
- Tell the student how many figures there are.
- Recommend describing figures **per chapter, when they start studying that chapter**, with `/study-library:describe-figures <slug> <chapter>`, rather than all at once.
- Figures without descriptions still work: when one is needed, it gets viewed and described then.

## 6. Finish
`books/_library.md` is updated automatically. Then:
- if `CLAUDE.md`'s "About me" mentions a course, add a line under it mapping this book to that course if that's useful;
- tell the student the book is ready, and suggest a first thing to try, e.g. "Ask me anything from chapter 1, or try `/study-library:quiz` on a topic."
