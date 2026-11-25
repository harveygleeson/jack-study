---
name: flashcards
description: Make Anki-importable flashcards (basic and cloze) from a chapter, section, topic or the student's weak areas, grounded in their textbooks with page references. Use when the user asks for flashcards, Anki cards or spaced-repetition material.
---

# Flashcards (Anki)

## Scope
Find out the topic, chapter or section, or use "weak areas" from `progress.md`. Look it up in `books/` and read the source text (see the `look-up` skill). Cards must come from their books.

Roughly: 15–30 cards per textbook section, 40–80 per chapter. Ask before making more than about 100.

## Good cards
- **One fact per card.** Questions are specific and answers are short. Split lists into several cards, or use cloze.
- Prefer **why/how** and **clinical-link** cards over pure trivia, but include must-know numbers and values (normal ranges, key thresholds).
- Use **cloze** for definitions, sequences and classic associations: `{{c1::Aldosterone}} increases Na⁺ reabsorption in the {{c2::collecting duct}}`.
- Add the source to the back of every card: `<br><small>Guyton ch. 27 p. 330</small>`.
- Figure cards are fine. Put the question on the front and the figure reference plus answer on the back. (Images aren't embedded, because Anki import can't bring the image file along. Name the figure and page instead.)

## File format
Save to `notes/flashcards/<book-or-topic>-<chapter-or-topic>.txt` as UTF-8, **tab-separated**. Basic and cloze cards go in **separate files** because they use different note types.

Basic file:
```
#separator:tab
#html:true
#notetype:Basic
#deck:Study::<Book>::<Chapter>
#tags column:3
<front>	<back with source>	<tags>
```
Cloze file: same header with `#notetype:Cloze`, two columns (`text`, `extra`), then tags in column 3.

Tags: use space-separated words like `ch27 renal physiology` (no spaces inside a tag; use `_`). No literal tab characters or newlines inside a field; use `<br>` for line breaks.

## Finish
Tell the student:
- the file path(s) and the card count;
- **how to import**: open Anki, choose File → Import, pick the `.txt` file. The settings fill in automatically from the file header. Check the preview, then Import.
- that they can ask for cards on another topic, or "harder" or "fewer" cards.
