# Editing a resume in Google Docs through Chrome

Learned the hard way. The Docs editor is a canvas, so most page-reading tools see nothing.

## Read
- `docs.google.com/document/d/<id>/mobilebasic` serves plain HTML; `get_page_text` works there.
- Drive row IDs are on `[data-id]` attributes. If a JS filter blocks token-like output, double-click the row and read the URL instead.

## Copy
- `docs.google.com/document/d/<id>/copy` creates a copy in My Drive **root**. Rename it via the title field, then move it to the right folder.
- File → Make a copy keeps the original folder.

## Find & Replace (cmd/ctrl+shift+h)
- 🔴 Wait ~3 s and **zoom to confirm the caret is in the Find field before typing.** Unfocused typing has replaced the entire document.
- Never select-all unless you've verified which field has focus.
- `\n` in Replace is inserted literally, even with regex on. To add a paragraph: replace to a unique literal marker, Find the marker, close the dialog (the selection persists), press Return, then type.
- Delete a paragraph: regex on, Find `exact text\n`, Replace with empty.
- Bold: Find the text, close the dialog, cmd/ctrl+b.
- 🔴 **Never replace a span that contains a bold run.** The replacement takes the formatting of its first character, so the bold collapses. Split around the bold: replace the prefix, then delete the suffix.

## Page budget
- Count wrapped **lines** (~115 chars/line including bold labels); a full page is ~64–65 lines. Recheck after every change.
- Verify in both mobilebasic and the editor (scroll to the end); mobilebasic hides page breaks.

## Export
- `docs.google.com/document/d/<id>/export?format=pdf`
- Verify page count mechanically (`pdfinfo` → `Pages: 1`), not by eye.
- If an older PDF has no matching Doc, check `pdfinfo` Producer to see how it was made before trying to patch it.
