---
name: describe-figures
description: Write searchable text descriptions for the figures in a converted textbook (a whole book or one chapter), so diagrams can be found by what they show, not just their caption. Use when the user asks to describe figures, or before studying a figure-heavy chapter.
---

# Describe figures

The tool is `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/studylib.py"`, shortened to **studylib** below.

Arguments: a book slug and optionally a chapter: the file prefix such as `ch25` (the `#` column of `_index.md`; non-chapter files are `x01`, `x02`…). With no chapter, ask whether they mean the whole book, and warn that a whole book can mean 1,000+ figures and a lot of usage. Suggest going chapter by chapter.

## Steps
1. List what's left: `studylib figures books/<slug> --section <ch25> --undescribed`. Each line has: id, page, absolute image path, chapter file, caption. Tell the student how many there are.
2. Work in batches of about 15–25 figures. For each figure, view the image (Read the image path). Then write the description.
   - **If you can run subagents**, give each batch to a subagent in parallel. Give it the list lines and these style rules, and have it write its results to `notes/.figdesc-<slug>-<section>-<batch>.json`. Otherwise do the batches yourself.
3. Save each batch's JSON `{ "<id>": "<description>", ... }` with `studylib describe books/<slug> <file.json>`. Then delete the JSON file.
4. Report how many were described, and mention any figures that were unreadable, decorative or duplicates.

## Description style
Write 1–4 sentences, dense with searchable terms:
- **What kind of image it is** (labelled diagram, histology micrograph with stain and magnification, CT/MRI/X-ray, flowchart, graph, table rendered as image, clinical photo).
- **Every label and structure shown**, using the book's own terms.
- **Relationships the image shows**: what connects to what, flow direction, axes and trends of a graph.
- **The key teaching point**, if it's obvious.

Example: *Labelled sagittal diagram of the female pelvis showing urinary bladder, uterus, pubic bone, urethral sphincter, sacrum, anus, and the pudendal nerve running from the sacral spinal cord to the external urethral sphincter. Illustrates the somatic (pudendal) innervation involved in voluntary control of micturition.*

Skip purely decorative images (chapter-opening photos, icons, logos) with a short description like "Decorative chapter-opening photograph". That way they count as done.
