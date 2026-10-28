# Software Requirements Specification — LaTeX conversion

Converted from `PA2-SoftwareRequirementsSpecification (1).docx`.

## Files

- `main.tex` — minimal document entry point.
- `preamble.tex` — packages, fonts, colors, page geometry, headings, and repeating header/footer.
- `frontmatter.tex` — cover, table of contents, and objectives pages.
- `body.tex` — ordered list of the eleven section files.
- `sections/` — editable document content. Each numbered section has its own directory, and each second-level subsection has a numbered file such as `2.1-purpose-and-scope.tex`.
- `assets/hcmus_logo.png` — university logo extracted from the source Word document.
- `main.pdf` — compiled preview.

## Compile

Use an up-to-date TeX installation with XeLaTeX, TikZ, fontspec, longtable, hyperref, and the Liberation Sans font. From the project directory:

```sh
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

You can also use `latexmk -xelatex main.tex`.

## Conversion notes

- The cover is recreated with **editable LaTeX text, a native colored rectangle, and the extracted logo**; the cover itself is not a rasterized screenshot.
- The Word cover clips the bottom of the word "Requirements". This version retains the visual arrangement but allows the complete word to be seen.
- The unpopulated Word table-of-contents field is replaced with a generated LaTeX table of contents.
- The main content retains its original words and table cells as exported from Word; the document's pagination and line breaks differ from Word because of LaTeX typesetting. Some table stylistic details are approximations.
- The document is 17 pages in the supplied LaTeX compilation versus 19 pages in the Word rendering.
