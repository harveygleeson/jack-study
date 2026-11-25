# Setting up your study library

This lets Claude **look things up in your textbooks** instead of you uploading huge PDFs to every chat. Claude searches the books, reads just the parts it needs, shows you diagrams, cites page numbers, and keeps track of what you've studied. Setup takes about 15 minutes, and you do it once.

You need: Windows, the Claude desktop app (signed in), and your textbook PDFs.

---

## 1. Install Git for Windows (one time)
Claude uses it to download the study tools.
1. Go to **https://git-scm.com/downloads/win** and download the installer.
2. Run it and click **Next** through everything. The defaults are fine.

## 2. Make a study folder
Create a folder, for example `Documents\Study`. Your books and notes will live here, and only on your computer.

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
When it asks, choose to install it **for you (user)**. Then close and reopen the Code tab, or type `/reload-plugins`.

> If that doesn't work, try the menus instead: **Customize → Plugins → Add → Add marketplace**, enter `harveygleeson/jack-study`, then install **study-library**. If you're still stuck, message Harvey.

## 5. Run setup
Type:
```
/study-library:study-setup
```
Claude creates the folders, asks you a few quick questions (your course, exam dates, how you like explanations), and installs a small tool it needs to read PDFs. Click **Allow** when it asks.

## 6. Add your first book
Type something like:
```
add this book: C:\Users\<you>\Downloads\Guyton Physiology.pdf
```
(Tip: in File Explorer, right-click the PDF, choose **Copy as path**, and paste it.)

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

**Flashcards:** they're saved in `notes\flashcards\`. In Anki, choose **File → Import**, pick the file, and click Import.

**Diagrams:** before you start a diagram-heavy chapter, you can say *"describe the figures in chapter 27"*. That makes them searchable by what they show. It's optional, and it uses a fair amount of your Claude usage, so do it chapter by chapter.

## Getting updates
When Harvey improves the tools: type `/plugin`, go to **Marketplaces**, choose **jack-study**, then **Update**. You can turn on **auto-update** on the same screen. If Harvey says the instructions file changed, also run `/study-library:study-setup` again. It keeps your own notes.

## Good to know
- Everything stays on your computer. The books never go anywhere except into Claude's answers when it reads a passage.
- Your notes, progress and flashcards are plain files in your Study folder. Back the folder up (e.g. OneDrive) if you like.
- If a book comes out badly (for example a scanned book), Claude will tell you, so you don't get answers from garbled text.
