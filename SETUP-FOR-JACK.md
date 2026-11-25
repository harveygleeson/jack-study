# Setting up your study library

This lets Claude **look things up in your textbooks** instead of you uploading huge PDFs to every chat. Claude searches the books, reads just the parts it needs, shows you diagrams, cites page numbers, and keeps track of what you've studied. Setup takes about 15 minutes, and you do it once.

You need: a Mac, the Claude desktop app (signed in), and your textbook PDFs.

---

## 1. Make sure your Mac has Git (one time)
Claude uses Git to download the study tools. Most Macs need a quick one-time install.
1. Open **Terminal**: press ⌘ Space, type `Terminal`, and press Enter.
2. Type this and press Enter:
   ```
   git --version
   ```
3. If it prints a version number (like `git version 2.39…`), you're done. Close Terminal.
   If a window pops up asking to install the **command line developer tools**, click **Install** and wait a few minutes for it to finish. You don't need Xcode itself.

## 2. Make a study folder
In Finder, create a folder called **Study** inside **Documents**. Your books and notes will live here, and only on your Mac.

## 3. Open Claude Code in that folder
1. Open the Claude desktop app and switch to the **Code** tab.
2. Choose **your Study folder** as the folder to work in (local, not cloud).

## 4. Install the study tools
In the Code tab, with your Study folder open, type each line and press Enter:

```
/plugin marketplace add harveygleeson/jack-study
```
```
/plugin install study-library@jack-study
```
When it asks, choose to install it **for you (user)**. Then type `/reload-plugins`, or close and reopen the Code tab.

> If that doesn't work, try the menus instead: **Customize → Plugins → Add → Add marketplace**, enter `harveygleeson/jack-study`, then install **study-library**. If you're still stuck, message Harvey.

## 5. Run setup
Type:
```
/study-library:study-setup
```
Claude creates the folders, asks you a few quick questions (your course, exam dates, how you like explanations), and installs a small tool it needs to read PDFs. Click **Allow** when it asks.

## 6. Add your first book
Type `add this book:` and then give the PDF's location. Two easy ways:
- **Drag the PDF** from Finder into the message box. That pastes its location.
- Or, in Finder, right-click the PDF, **hold the Option key**, and choose **Copy "…" as Pathname**. Then paste it.

It should look something like:
```
add this book: /Users/<you>/Downloads/Guyton Physiology.pdf
```

A big textbook takes about 5–20 minutes to convert. Claude checks that it came out well and tells you when it's ready. Repeat for each book.

---

## Using it
Open the **Code** tab in your **Study** folder and just talk to it:

- *"Explain the countercurrent multiplier, and show me the diagram from my book"*
- *"What's the difference between nephritic and nephrotic syndrome? Compare what my books say"*
- *"Quiz me on renal physiology, clinical vignettes"*, or type `/study-library:quiz`
- *"Make Anki flashcards for chapter 27"*, or `/study-library:flashcards`
- *"My pharmacology exam is on 12 March. Make me a revision plan"*, or `/study-library:revision-plan`
- *"What should I study today?"*

Answers come with page references like *(Guyton ch. 27, p. 330)*, so you can check the book.

**Flashcards:** they're saved in `notes/flashcards/` inside your Study folder. In Anki, choose **File → Import**, pick the file, and click Import.

**Diagrams:** before you start a diagram-heavy chapter, you can say *"describe the figures in chapter 27"*. That makes them searchable by what they show. It's optional, and it uses a fair amount of your Claude usage, so do it chapter by chapter.

## Getting updates
When Harvey improves the tools: type `/plugin`, go to **Marketplaces**, choose **jack-study**, then **Update**. You can turn on **auto-update** on the same screen. If Harvey says the instructions file changed, also run `/study-library:study-setup` again. It keeps your own notes.

## Good to know
- Everything stays on your Mac. The books never go anywhere except into Claude's answers when it reads a passage.
- Your notes, progress and flashcards are plain files in your Study folder. Back the folder up (e.g. iCloud Drive) if you like. Each converted book also takes about as much space again as its PDF.
- If a book comes out badly (for example a scanned book), Claude will tell you, so you don't get answers from garbled text.

<details>
<summary>On Windows instead?</summary>

The steps are the same, except for step 1: install **Git for Windows** from https://git-scm.com/downloads/win (the default options are fine). To copy a file's location, right-click the PDF in File Explorer and choose **Copy as path**.
</details>
