# Cover Department Layout Design

## Intent

Keep the university logo and department identification together on the cover instead of splitting them across two pages. The department text must be ragged-left.

## Selected approach

Retain the logo in its existing bottom-left TikZ node and add a separate TikZ text node immediately to its right. Use `anchor=west` and `align=left` so all three lines share a left edge.

## Changes

- Move “Software Engineering Department”, “Faculty of Information and Technology”, and “University of Science” into the cover-page TikZ picture.
- Position the text vertically alongside the logo.
- Remove the separate departmental title-page block and its associated `\clearpage`.
- Keep all other cover elements unchanged.
- The table of contents becomes page 2; subsequent page-dependent header/footer numbering must be adjusted so content numbering remains correct.

## Alternatives considered

- A separate text node was selected because it allows precise independent positioning.
- A combined logo-and-text node was rejected because it is harder to tune and maintain.

## Verification

Compile twice with XeLaTeX, confirm the PDF page count decreases by one, inspect the cover layout, and confirm the department text is left-aligned and no longer appears on a separate page.
