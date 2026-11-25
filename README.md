# jack-study

A Claude Code plugin that turns big textbook PDFs into a study library Claude can **search** instead of loading whole books into a chat. It also adds study skills: quizzes, Anki flashcards and revision plans.

- **For Jack (setting it up and using it):** see [SETUP-FOR-JACK.md](SETUP-FOR-JACK.md)
- **For maintaining it:** read on

## How it works

```
Study\                         ← Jack's folder; lives only on his computer, never in this repo
  CLAUDE.md                    ← rules: look things up before answering, cite printed pages…
  progress.md                  ← exams, topics studied, quiz log, weak areas
  notes\                       ← flashcards, quizzes, revision plans Claude writes
  books\
    _library.md
    guyton-14e\
      _index.md                ← chapter/section → file:line map, page-number rules
      _book-index.md           ← the book's own back-of-book index
      ch27-….md                ← one file per chapter, <!-- page 1160 | printed 1144 --> markers
      figures\ch27\ch27-007.png
      figures.json             ← figure manifest (caption, page, description)
      source.pdf               ← original, for rendering exact pages
```

Claude greps the Markdown and reads about 100 lines around each hit, so it never holds a whole book. Figures are extracted as images and linked where they appear. Captions are searchable, and written descriptions can be added (`describe-figures`). When the extracted text is messy, Claude renders the original PDF page and looks at it.

## Repo layout

```
.claude-plugin/marketplace.json     this repo is its own plugin marketplace ("jack-study")
plugins/study-library/
  .claude-plugin/plugin.json
  scripts/studylib.py               the converter / helper CLI (runs with `uv run`, deps inline)
  templates/CLAUDE.md, progress.md  copied into Jack's folder by study-setup
  skills/
    study-setup/      first run: folders, CLAUDE.md, installs uv
    add-book/         inspect → convert → quality check
    look-up/          how to search, cite, view figures and original pages (auto-used)
    describe-figures/ batch figure descriptions (per chapter)
    quiz/             SBA / vignette / short-answer quizzes, logs to progress.md
    flashcards/       Anki-importable .txt (basic + cloze)
    revision-plan/    exam timetable with spaced review
```

## studylib.py

Needs only [uv](https://docs.astral.sh/uv/). It fetches Python and `pymupdf4llm` itself.

```bash
uv run plugins/study-library/scripts/studylib.py inspect book.pdf          # TOC, scanned?, page offset, planned split
uv run plugins/study-library/scripts/studylib.py convert book.pdf --library books --slug guyton-14e --title "Guyton & Hall 14e"
uv run plugins/study-library/scripts/studylib.py check books/guyton-14e
uv run plugins/study-library/scripts/studylib.py figures books/guyton-14e --section ch27 --undescribed
uv run plugins/study-library/scripts/studylib.py describe books/guyton-14e descs.json   # {"ch27-007": "…"}
uv run plugins/study-library/scripts/studylib.py page books/guyton-14e 330 --printed     # → PNG path
```

`convert` is resumable: it checkpoints after each chapter, so re-running it continues where it stopped. Scanned PDFs (no text layer) are detected by `inspect` and need OCR first.

## Developing

Test the plugin locally without installing it:

```bash
mkdir -p ~/StudyTest && cd ~/StudyTest
claude --plugin-dir /path/to/jack-study/plugins/study-library
# then: /study-library:study-setup, "add this book: ~/Downloads/x.pdf", …
```

Validate before pushing:

```bash
claude plugin validate ./ && claude plugin validate ./plugins/study-library
```

**Releasing:** `plugin.json` has no `version`, so every pushed commit counts as a new version. Jack picks it up on his next marketplace update, or automatically if he turns on auto-update. If you change `templates/CLAUDE.md`, tell him to re-run `/study-library:study-setup` to refresh his copy. It only replaces the managed block and keeps his own notes.

**Never commit books.** They're copyrighted and huge. `.gitignore` blocks PDFs and `books/` folders as a safety net.
