---
name: revision-plan
description: Build or update a day-by-day revision timetable for an upcoming exam, based on the exam date, the chapters it covers, the size of each chapter, and the student's progress and weak areas. Use when the user mentions planning revision, a study schedule, or an exam date.
---

# Revision plan

## Gather
- **The exam**: date, subject, which chapters or topics it covers. Check `progress.md` and `CLAUDE.md` "About me" first, and only ask for what's missing.
- **Time**: about how many hours per day they can study, days off, and other commitments. Ask once and keep it brief.
- **What's covered**: map the topics to book chapters using `books/<slug>/_index.md`. Use page counts to estimate size. A rough guide is about 6–10 dense textbook pages per hour for first-pass study, with half that again for active review.
- **Where they stand**: "Topics studied", confidence ratings and "Weak areas" in `progress.md`.

## Build the plan
- Work backwards from the exam: **first pass** of unstudied material, then **spaced review** (revisit each topic about 1, 3 and 7 days after first study), then **mixed practice** in the final days.
- Weight time toward weak areas and high-yield, heavily examined topics.
- Every study block should include active recall: a quiz (`/study-library:quiz <topic>`) or flashcards. Not just reading.
- Leave buffer days, roughly 1 in 7. Plans always slip.
- Keep the last day light: review weak-area flashcards and rest.

## Save
Write `notes/revision-plan-<exam>-<date>.md` as a table:

| Date | Focus (chapter / pages) | Activity | Done |
|---|---|---|---|

Under the table, add a short "If you fall behind" section that names which topics to compress or drop first.

Add the exam to the "Exams" table in `progress.md` if it isn't there.

## Keeping it current
When the student comes back and says what they've done (or asks "what should I do today?"), read the latest plan. Mark finished rows, and if they're behind, rebalance the remaining days and say what changed.
