# PA2 Report Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete all approved PA2 report gaps using PA0, PA1, GitHub, and user-confirmed evidence while keeping the existing LaTeX layout stable.

**Architecture:** Edit the existing modular section files in place. Keep report claims traceable to project evidence, distinguish static mockup review from runtime testing, and use the shared font commands already defined in `preamble.tex`.

**Tech Stack:** XeLaTeX, `longtable`, `fontspec`, GitHub issue links

**Spec:** `docs/superpowers/specs/2026-10-31-pa2-report-completion-design.md`

## Global Constraints

- Preserve Sections 1--11 and their current numbering.
- Contributions are 20% per member and total 100%.
- Review date is 31 October 2026 and includes all five members.
- Do not claim interactive accessibility testing from static mockups.
- Keep Section 9 extension guidance as a normal note.
- Use Inter for all Section 8 image subtitles and captions.

## Review Focus

- Vietnamese names and prose must render without missing glyphs.
- Long GitHub links must not overflow table cells.
- Section 8 results must not imply unperformed runtime testing.
- Section 10 resolutions must match the actual Git/GitHub history.
- AI disclosures must cover all members without inventing specific prompts or tools.

---

### Task 1: Complete member contributions and remove stale instructions

**Files:**
- Modify: `pa/PA2/src_latex/sections/01-member-contribution-assessment/01-member-contribution-assessment.tex`
- Modify: `pa/PA2/src_latex/sections/04-stakeholders/04-stakeholders.tex`

**Interfaces:**
- Consumes: PA0 identities/roles and GitHub Issues #11--#19.
- Produces: completed Section 1 and clean completed Section 4.

- [ ] Replace Section 1’s instruction and placeholder rows with the five approved 20% rows and evidence links.
- [ ] Remove the obsolete instructional paragraph from Section 4 without changing its stakeholder table.
- [ ] Verify five IDs are present and percentages total 100.

### Task 2: Complete Section 8 and retain Section 9 as a note

**Files:**
- Modify: `pa/PA2/src_latex/sections/08-prototype-mockups/08-prototype-mockups.tex`
- Modify: `pa/PA2/src_latex/sections/09-requirements-traceability-matrix/09-requirements-traceability-matrix.tex`

**Interfaces:**
- Consumes: approved static-review wording and existing `\bodyfont` command.
- Produces: honest accessibility findings, Inter subtitles/captions, and a non-placeholder Section 9 note.

- [ ] Apply `\bodyfont` explicitly inside `\scrimg` subtitles and all figure captions.
- [ ] Replace four accessibility placeholders with approved conservative findings.
- [ ] Convert Section 9’s bracketed instruction into an explanatory note.
- [ ] Verify no `điền sau khi kiểm tra` remains.

### Task 3: Complete requirements review and AI disclosure

**Files:**
- Modify: `pa/PA2/src_latex/sections/10-requirements-review/10-requirements-review.tex`
- Modify: `pa/PA2/src_latex/sections/11-ai-usage-log/11-ai-usage-log.tex`

**Interfaces:**
- Consumes: approved review facts, Git history, issue ownership, and team AI-use statement.
- Produces: final baseline review record and complete AI usage log.

- [ ] Add review date, participants, baseline statement, and four issue/resolution rows to Section 10.
- [ ] Add five member-level AI rows and one team-level LaTeX creation/refactoring row to Section 11.
- [ ] State human verification and editing for every AI entry.
- [ ] Verify all five names appear and no example placeholder remains.

### Task 4: Validate the completed report

**Files:**
- Verify: `pa/PA2/src_latex/**/*.tex`

**Interfaces:**
- Consumes: Tasks 1--3 outputs.
- Produces: warning-free, correctly numbered PDF build.

- [ ] Search for remaining instructional placeholders and review each match.
- [ ] Run XeLaTeX twice from `pa/PA2/src_latex`.
- [ ] Scan the final log for warnings, errors, missing characters, and overfull/underfull boxes.
- [ ] Verify TOC numbering remains Sections 1--11.
- [ ] Remove temporary verification artifacts.
