# PA3 Section 5 — Data design

This directory is the reproducible design source and verification evidence for
[Section 5](../../../pa/PA3/src_latex/sections/05-data-design/05-data-design.tex).
It is an executable design reference, **not an automatic production migration**.

## Artifacts

- [generate_design.py](generate_design.py): canonical 17-table/126-column model,
  constraints, FK definitions, index predicates and rationales.
- [schema.sql](schema.sql): generated DDL; 27 FKs and 25 explicit indexes in
  addition to indexes owned by PK/UNIQUE constraints.
- [rules.sql](rules.sql): cross-row triggers, deferred assertions, public view,
  protected contact functions, Claim/report reference routines, grants and RLS.
- [erd.dbml](erd.dbml): portable textual diagram source with every table/column/FK.
- [native ERD](../../../pa/PA3/src_latex/sections/05-data-design/05.1-erd.tex): three
  vector TikZ diagrams included directly in the report. The accompanying
  [relationship matrix](../../../pa/PA3/src_latex/sections/05-data-design/05.1-relationships.tex)
  states every FK's cardinality, nullability and delete policy.
- [model.json](model.json): generated machine-readable model used to compare
  physical columns/indexes with the specifications.
- [verification-results.json](verification-results.json): actual SQL run results.
- [evidence.md](evidence.md): requirements/OOD mapping and verification limits.

## Regenerate and verify

From the repository root (Python 3 and Node.js 20+):

```powershell
python docs/design/database/generate_design.py
npm.cmd --prefix docs/design/database ci --ignore-scripts --no-audit --no-fund
npm.cmd --prefix docs/design/database test
```

The test uses pinned PGlite 0.5.16 and a **new in-memory database**. It does not
connect to or modify a live Supabase instance. It creates a minimal test-only
`auth.users(id)` and `anon`/`authenticated` roles, then applies `schema.sql` and
`rules.sql`. Real Supabase Auth must supply the managed auth schema during deployment.

Build the report twice from `pa/PA3/src_latex`:

```powershell
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

Generated SQL, JSON, DBML and table/index/relationship LaTeX must be regenerated
together. The ERD layout, prose and `rules.sql` are maintained manually. No
additional diagram renderer or shell escape is required to compile the report.

## Security and deployment contract

1. Use a dedicated migration owner. Never use that owner, a superuser or a
   Supabase service-role key as the ordinary application database identity.
2. `lf_api`, `lf_auth`, `lf_catalog` are **NOLOGIN permission groups**. Deployment
   assigns them to separate backend connection identities/pools as needed; no
   credentials are in this repository. Verify role-creation permissions before
   applying the reference scripts to a particular hosting environment.
3. `app`/`private` are not browser-accessible Data API schemas. PUBLIC grants are
   revoked. Never grant their tables/routines to Supabase `anon`/`authenticated`.
   The SPA calls Express; only authorized image URLs are read from Storage.
4. `lf_api` cannot SELECT private contact tables. Contact reads/writes go through
   narrow SECURITY DEFINER functions with fixed `search_path` and qualified names.
   `lf_auth` may read school-email columns, not phone numbers; `lf_catalog` may
   handle school-request PII, not user contacts.
5. RLS policies admit the trusted backend groups, not individual end users.
   **Actor/viewer UUID function arguments are not authentication.** Express must
   derive them from a verified identity, enforce ownership/role and never accept
   arbitrary actor IDs from request JSON. Contact reads and their checks share
   the read-only REPEATABLE READ transaction specified in OOD.
6. Server DTOs use explicit allowlists. Public data uses `app.public_posts` and
   contains no contact, answer, private identifier, storage location or proof key.
   Claim answers and evidence are authorized only for the sender/post owner.
   Evidence objects use private Storage and short-lived signed URLs, not public
   URLs. A database object key does not prove that Storage ACL/file bytes are safe.
7. Application transactions follow OOD's sorted-User-then-Post lock ordering.
   Partial unique indexes are the final uniqueness guard. The embedded test
   exercises integrity/rollback, **not parallel sessions or load**.
8. Keep operations append-only/soft-delete as specified. Retry records in
   `integration_tasks` support explicit API/CLI retries; they do not require a
   memory-consuming background worker or claim transactional rollback of Storage/Auth.

## Design choices carried from PA3 OOD

- Post type LOST/FOUND is independent of lifecycle status.
- `CLOSED` means owner-deleted or admin-removed, distinguished by `close_reason`.
  Owner mutation is restricted to ACTIVE. REPORTED retains `previous_status`.
- Minimum one/max five post images follows the current 4.1/4.2 decision. The
  image-optional interpretation has not silently replaced that baseline.
- Claimant contact is the verified school email, as explicitly chosen in 4.2.
- Handled reports no longer contribute to the next threshold, but the
  `(post_id, reporter_id)` unique constraint preserves the once-per-person rule.
- A materialized search vector and externally synchronized Auth profile/email
  are the documented technical exceptions/replicas; no redundant counters or
  copied university/category names are stored in Post.
- Notification Claim/Post context and message/event classification, plus settled
  Report audit context, are deliberate 3NF exceptions for uniform routing and
  queue/history storage. CHECKs and triggers reject inconsistent replicas; their
  Claim/audit determinants are immutable. See the report's normalization review.
