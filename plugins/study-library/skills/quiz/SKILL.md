---
name: quiz
description: Quiz the student on a topic, chapter or weak area from their textbooks — single-best-answer MCQs, clinical vignettes, short-answer and figure questions — with feedback, page references and results logged to progress.md. Use when the user asks to be quizzed, tested or asked questions.
---

# Quiz

## Set up
- **Topic.** Use what the student asked for. If they didn't say, offer: weak areas from `progress.md`, the most recent topic studied, or a chapter for an upcoming exam.
- **Format.** The default is 5–10 questions, **one at a time**. The student can ask for more or fewer, a timed feel, or "all at once".
- **Question styles.** Mix these unless they ask for one style:
  - **Single best answer (SBA/MCQ)** with 5 options (A–E) and plausible distractors.
  - **Clinical vignette**: a short patient scenario that tests application, not just recall ("A 54-year-old man presents with…"). These suit anything clinical, physiology and pharmacology.
  - **Short answer / explain**: "Explain why…", "What happens to X when Y?"
  - **Figure question**: point to a figure (give the image path and figure number) and ask about what it shows.
- **Level.** Match their course and year from `CLAUDE.md` "About me". Increase difficulty if they're scoring well.

## Ground every question in the books
Before writing questions, look the topic up in `books/` (see the `look-up` skill) and read the relevant sections. Every question and answer must be supported by their textbooks. Note the source page for each question as you go. Don't write questions from general knowledge the books don't cover unless the student asks for that.

## During the quiz
- Ask one question and wait for the answer.
- After each answer, say right or wrong, then explain **why**. For an SBA, also explain why the best distractor is wrong. Cite the source *(Book ch. X, p. Y)*.
- If they're wrong or unsure, give a one-line memory hook or a link to a related concept.
- Don't reveal answers ahead of time, and don't hint in the question wording.

## Finish
1. Give the score, then list the **concepts missed** (concepts, not question numbers), each with its page reference to re-read.
2. Update `progress.md`:
   - add a row to the "Quiz log" (date, topic, score, missed concepts);
   - add missed concepts to "Weak areas to revisit";
   - remove weak areas they've now answered correctly twice or more.
3. Offer next steps: flashcards for the missed concepts (`/study-library:flashcards`), a re-quiz on only the misses, or moving on.
4. If they want to keep the questions, save them to `notes/quizzes/<date>-<topic>.md` with answers and explanations at the end.
