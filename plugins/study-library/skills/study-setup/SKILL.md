---
name: study-setup
description: Set up (or refresh) a study workspace in the current folder — creates books/, notes/, progress.md and CLAUDE.md, and makes sure the PDF conversion tool (uv) works on this computer. Use on first run, after a plugin update, or when the user says the study tools aren't working.
---

# Study workspace setup

You are setting up a study workspace for a student who is **not a programmer**. Do the technical work yourself, explain in plain language, and ask before installing anything.

The plugin's files are in `${CLAUDE_PLUGIN_ROOT}`. The conversion tool is `${CLAUDE_PLUGIN_ROOT}/scripts/studylib.py`.

## 1. Check the folder
- The workspace is the current working directory. If it looks like the wrong place (for example a system folder, the home folder itself, or a code project), say so and suggest making a folder such as `Documents\Study` and opening Claude there.
- Create the folders `books/`, `notes/` and `notes/flashcards/` if they are missing. Leave anything that already exists alone.

## 2. CLAUDE.md
- If there is no `CLAUDE.md`, copy `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md` here.
- If `CLAUDE.md` exists, replace **only** the text from `<!-- study-library:start` through `<!-- study-library:end -->` with the same block from the template. Keep everything outside the block (the student's "About me" section) exactly as it is. If the markers are missing, add the template block at the top and keep the existing content below it.
- If the "About me" section is still empty, ask the student those questions now (course and year, upcoming exams, how they like explanations, what they find hard) and fill it in. Keep this short and friendly. They can skip it.

## 3. progress.md
If `progress.md` is missing, copy `${CLAUDE_PLUGIN_ROOT}/templates/progress.md`. Add any exam dates they just gave you.

## 4. Conversion tool (uv)
The PDF converter runs with **uv**, which installs Python and the libraries automatically.
1. Run `uv --version`. If it works, go to step 5.
2. Try the usual install location directly: `~/.local/bin/uv --version` (on Windows this is `%USERPROFILE%\.local\bin\uv.exe`). If that works, use that full path for uv for the rest of this session, and tell the student that restarting the Claude app will make plain `uv` work.
3. Otherwise explain: "To convert PDFs I need a small free tool called uv (from Astral). It installs into your user folder and doesn't need admin rights. OK to install?" Then, with permission:
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   Then use the full path from step 2.

## 5. Smoke test
Run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/studylib.py" --help`. The first run downloads Python and the PDF libraries, which takes a minute or two. If it fails, read the error and fix it (common causes: no internet, antivirus blocking, uv not on PATH). Don't hand raw errors to the student without explaining them.

## 6. Finish
Tell the student, in a few lines:
- the workspace is ready, and what's in it;
- next step: put a textbook PDF somewhere (e.g. Downloads) and say **"add this book: <path>"** or run `/study-library:add-book`;
- after that they can just ask questions, or use `/study-library:quiz`, `/study-library:flashcards` and `/study-library:revision-plan`.
