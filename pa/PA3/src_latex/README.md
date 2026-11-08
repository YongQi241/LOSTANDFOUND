# Software Design — LaTeX conversion

Converted from `../T011_PA3.docx`, following the organization and visual style of `pa/PA2/src_latex`.

## Files

- `main.tex` — document entry point.
- `preamble.tex` — packages, embedded fonts, colors, geometry, headings, and repeating header/footer.
- `frontmatter.tex` — editable cover, generated table of contents, and objectives page.
- `body.tex` — ordered section includes.
- `sections/` — one editable source file for each PA3 section.
- `assets/hcmus_logo.png` — logo extracted from the PA3 Word document.
- `assets/fonts/` — vendored fonts shared with the PA2 LaTeX source.

## Compile

Use XeLaTeX from this directory:

```sh
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

Alternatively, run `latexmk -xelatex main.tex`.

## Conversion notes

- Cover text, headings, placeholder instructions, tables, and lists remain editable.
- The Word table-of-contents field is replaced by a generated LaTeX table of contents.
- The source Word file is an unfilled PA3 template; this conversion preserves its placeholders rather than inventing project content.
