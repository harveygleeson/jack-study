---
name: look-up
description: How to find and read material in the study library (converted textbooks in books/) — searching, citing printed pages, using the back-of-book index, viewing figures and original PDF pages. Use whenever answering a study question from the student's books, explaining a figure, or when extracted text looks garbled.
---

# Looking things up in the library

The tool is `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/studylib.py"`, shortened to **studylib** below.

## Find
1. **Search first.** Grep `books/` (case-insensitive) for the key term, its synonyms and its abbreviation, e.g. `GFR|glomerular filtration`. Medical terms come in variants: search both British and American spelling (haem/hem, oedema/edema, -aemia/-emia), the eponym and the descriptive name, and the drug class and drug name.
2. **Use the maps.** The section list in `books/<slug>/_index.md` gives `file:line` for every heading. The back-of-book index `_book-index.md` lists every page a term appears on (as printed page numbers; PDF page = printed + offset, shown in `_index.md`). It's the most reliable way to find *all* the places a topic is covered.
3. **Read narrowly.** Read about 50–200 lines around the hit with an offset. Widen only if the explanation continues. Several books may cover a topic. For a substantial question, check each relevant book and use the clearest, or compare them.

## Cite
Page markers look like `<!-- page 1160 | printed 1144 -->`. Cite the **printed** page number, the book's short name and the chapter: *(Guyton ch. 27, p. 330)*. If there's no printed number, cite "PDF p. 1160".

## Figures
In chapter files a figure looks like:
```
<!-- fig ch25-007 -->
![FIGURE 25.5 Nerves Innervating the Urinary System](figures/ch25/ch25-007.png)
> **Figure description (ch25-007):** ...      ← only if already described
```
- The caption (in the `![...]` text) and the description are searchable text.
- To actually see a figure, read its image file (the path is relative to `books/<slug>/`). Do this when the question depends on the diagram: spatial relations, labels, graphs, pathways.
- **After you view a figure that has no description, save one** so it's searchable next time. Write `{"<id>": "<description>"}` to a temporary JSON file, run `studylib describe books/<slug> <file.json>`, then delete the JSON file. Description style: see the `describe-figures` skill.
- When helping the student, point them to the figure (book, figure number, printed page) and give the image path so they can open it.

## When the text looks wrong
Converted text can be scrambled where the layout was complex: tables, sidebars, multi-column boxes, flowcharts drawn as vector graphics, equations. If a passage looks garbled, or a table or figure seems to be missing:
`studylib page books/<slug> <pdf-page>` renders that page of the original PDF as an image (add `--printed` if you're giving the printed number). View it and answer from the real page.

## Not in the books?
Say so clearly ("Your books don't cover X; here's the standard explanation…") before using general knowledge. Never invent page references.
