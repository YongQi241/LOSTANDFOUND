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

## Object-oriented design (Sections 4.2--4.6)

- `sections/04-object-oriented-design/04-object-oriented-design.tex` retains
  the domain model (4.1) and includes the completed design sections.
- `04.2-class-diagram.tex` contains the design decisions and class diagrams;
  `04.3-class-specifications.tex` specifies eight principal classes.
- `04.4-sequence-diagrams.tex` includes five editable `sequence-uc*.tex`
  diagrams covering five use cases, one diagram per use case;
  `04.5-state-machines.tex` defines Post, Claim and User lifecycles.
- `04.6-design-principles.tex` explains the principles and patterns actually
  used. `ood-diagram-styles.tex` supplies local TikZ styles.
- Diagrams are native LaTeX/TikZ: no PlantUML server, shell escape, image
  generation or additional rendering step is needed. Compile `main.tex`
  twice with XeLaTeX to resolve the table of contents and references.
- Section 4.2 explicitly records implementation refinements, including
  soft deletion, restoration after moderation, verified-account checks and
  private contact access. The existing 4.1 source is preserved.

## Data design (Section 5)

- `sections/05-data-design/05-data-design.tex` includes the three ERDs, complete
  FK/cardinality matrix, generated 17-table dictionary, 3NF review, index
  rationale and PA2 privacy/Claim review.
- Reproducible SQL, DBML, generator, pinned SQL verification tool and evidence
  are in [`docs/design/database`](../../../docs/design/database/README.md).
- Run the generator before editing generated SQL/table/index specifications;
  see that directory's README for verification commands and deployment limits.
