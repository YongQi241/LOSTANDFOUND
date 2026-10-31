# PA2 Report Completion Design

## Intent

Complete the remaining PA2 report content using verifiable project evidence while preserving the existing LaTeX structure and visual style. The final report should be submission-ready, disclose AI assistance honestly, and avoid claiming tests that were not performed.

## Goals

- Complete Section 1 with all five members, PA0 roles, equal 20% contribution, and GitHub evidence.
- Complete Section 10 with a 31 October 2026 review involving all five members.
- Record the known Section 7 numbering and flow-formatting corrections, plus the decision to migrate Sections 1--5 from DOCX to LaTeX.
- Complete Section 11 with one AI-usage entry per member and a separate entry for AI-assisted LaTeX creation/refactoring.
- Replace Section 8 accessibility placeholders with conservative static-review findings.
- Render every Section 8 image subtitle and figure caption with Inter.
- Remove obsolete instructional placeholders from completed Sections 1, 4, 10, and 11.
- Retain Section 9's PA3/PA4 guidance as an explicit note rather than a placeholder.

## Non-goals

- Do not claim keyboard navigation, focus order, runtime validation, or responsive behavior was interactively tested.
- Do not invent issue comments, review approvals, measurements, or individual AI prompts.
- Do not change functional requirements, use-case content, prototype images, or the Section 9 traceability rows.

## Evidence and factual basis

- PA0 PDF: member names, student IDs, and primary roles.
- PA1 PDF: previous responsibilities, collaboration approach, and precedent for AI disclosure.
- GitHub Issues #11--#19: PA2 ownership and completion tracking.
- Git history and merged work: Sections 2--9, Section 7 formatting correction, LaTeX migration, and document integration.
- User confirmation: all five members participated in the review on 31 October 2026; each receives 20%; all members used AI for drafts/suggestions and personally edited the output.

## Content design

### Section 1

Use five rows:

- 24127434 -- Đỗ Vĩnh Kỳ -- Team Lead / PM -- 20% -- overall integration, LaTeX migration/refactoring, final review (Issue #19 and repository commits).
- 24127374 -- Huỳnh Thái Hòa -- Business Analyst -- 20% -- Sections 2--4, 5.1, 5.3, and Section 7 review/fixes (Issues #11, #12, #16).
- 24127117 -- Nguyễn Anh Tá -- Designer / Architect -- 20% -- Sections 5.2, 6, and 8 (Issues #13, #15, #17).
- 24127357 -- Nguyễn Gia -- Developer -- 20% -- NFR feasibility contribution and cross-review (Issue #13).
- 24127490 -- Trần Thiên Phú -- Tester -- 20% -- Sections 5.4 and 9 (Issues #14 and #18).

Evidence will be expressed as clickable GitHub issue links and concise commit/PR references where available.

### Section 8

- Static contrast review: mark as provisionally acceptable for visible text/components, with final WCAG ratio measurement required during implementation.
- Labels: mark visible labels and colocated validation areas as present in the supplied form mockups.
- Keyboard: mark as not verifiable from static mockups; carry forward as an implementation acceptance check.
- Touch targets: mark as visually designed near the 44-by-44 px target, with exact verification deferred to implementation.
- Explicitly apply `\bodyfont` to the `\scrimg` subtitle and all three figure captions.

### Section 9

Replace italic bracketed template wording with a normal note explaining that the Design element and Test cases columns are intentionally reserved for extension in PA3 and PA4.

### Section 10

Add review metadata and a resolution table covering:

1. Section 7 was accidentally nested as Section 6.4; restored as standalone Section 7 and renumbered downstream sections.
2. Main, alternative, and exception flows were hard to read; numbered steps were reformatted onto separate lines consistently across use cases.
3. DOCX editing made style consistency and issue/PR review difficult; the report was migrated to modular LaTeX for standardized formatting, workflow management, and easier review.
4. Missing/incomplete Sections 1, 8, 10, and 11 plus template remnants were identified during final review and completed or converted into explicit notes.

State that the reviewed version becomes the PA2 requirements baseline.

### Section 11

Use six rows: one for each member and one team-level LaTeX entry. Identify tools generically as ChatGPT / AI assistants where exact per-member products are not verified. State that members checked drafts against PA0, PA1, PA2 requirements, GitHub issues, and team decisions, then rewrote and corrected the material before inclusion.

## Approaches considered

1. **Evidence-based full completion (selected):** completes all visible gaps, retains Section 9 guidance as a note, and distinguishes static review from unperformed interactive testing.
2. **Minimal table fill:** edits only Sections 1, 10, and 11; rejected because visible placeholders would remain elsewhere.
3. **Optimistic completion:** marks every accessibility item as passed; rejected because static mockups cannot prove interactive behavior or exact measurements.

## Verification

- Search the source tree for bracketed template instructions and `điền sau khi kiểm tra`; only deliberate notes may remain.
- Confirm Section 1 contributions total 100%.
- Confirm all five members and six AI-use disclosures are present.
- Build twice with XeLaTeX.
- Scan the final log for warnings, errors, missing characters, and overfull/underfull boxes.
- Confirm the generated table of contents still numbers Sections 1--11 correctly.
