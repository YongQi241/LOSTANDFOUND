# PA3 Section 5 — Bằng chứng và đối chiếu thiết kế

Ngày kiểm tra: **12/11/2026**. Phạm vi: thiết kế dữ liệu và SQL tham chiếu,
không phải nghiệm thu ứng dụng hoặc triển khai production.

## Checklist và liên kết

| Tiêu chí | Artifact / kết quả |
| --- | --- |
| 5.1 ERD: tables, keys, relationships, cardinalities | [3 ERD vector][erd], [ma trận 27 FK][relationships], [DBML][dbml]; 17 bảng, 126 cột; auth.users là bảng quản lý ngoài application |
| 5.2 Columns/types/PK/FK/NN/UNIQUE/CHECK | [Dictionary][specs], [schema.sql][schema], [rules.sql][rules]; ràng buộc liên bảng dùng trigger/routine, điều kiện cuối transaction dùng deferred constraint trigger |
| 5.3 Ít nhất 3NF / ngoại lệ | [Normalisation review][review]: FD/khóa ứng viên; ngoại lệ Notification/Report context, message/event, search_vector và Auth replica có lý do và cơ chế kiểm soát; T32 ghi sai context bị từ chối |
| 5.3 Indexes có rationale | [25 index bổ sung][indexes], predicate và truy vấn mục tiêu; không tạo trùng PK/UQ; chưa khẳng định đạt NFR load |
| Privacy / Claim PA2 | Ma trận dưới đây và các ca thực thi có kết quả ở cuối file |
| OOD–ERD consistency | User/Auth, Post/subtypes, Claim, private contact, report/audit, catalog và notification được ánh xạ bên dưới |
| Commit/link evidence | Source, script, package lock, JSON kết quả và PDF được version control; commit hash được báo sau khi commit để tránh tự tham chiếu hash trong nội dung commit |

## PA2/OOD → enforcement → evidence

| Nguồn | Ánh xạ / cơ chế | Bằng chứng chính |
| --- | --- | --- |
| [PA2 BR-01][br], [UC-05][uc05], [UC-07][uc07] | users PK/FK auth.users; is_verified + ACTIVE; Post/Claim guard | T04, T09 |
| [BR-02][br], [NFR-02][nfr], [UC-08][uc08] | private.post_details, private.user_contacts; public_posts allowlist; quyền schema/column/RLS/routine | T12, T13, T17, T23–T25, T30 |
| [UC-07 main/A3][uc07] | claims.post_id tham chiếu Post chung; FOUND cần answer; LOST cần message hoặc proof | T07–T09 |
| [UC-07 E2][uc07] | claim_pending_uq chỉ áp dụng PENDING | T10: chặn gửi trùng, cho gửi lại sau REJECTED |
| [UC-08][uc08] | claim_accepted_uq, Post lock, decide_claim cập nhật nguyên tử và notification | T13–T16: chọn một người, rollback và chống trạng thái dở dang |
| [UC-06][uc06] | RESOLVED không tự cấp liên hệ; câu hỏi khóa khi PENDING; lịch sử không DELETE dây chuyền | T17, T18, T26, T29 |
| [BR-03][br], [section 2 PA3][overview] | report_once toàn lịch sử; count PENDING; REPORTED + previous_status; KEEP/REMOVE có audit | T19–T22; tự động ẩn là chi tiết đã chọn ở PA3 |
| [UC-05 E2][uc05], [4.1/4.2][ood] | post_images.position 1–5 + unique; size/MIME check; deferred contact/min-image | T05–T06; min một ảnh là quyết định PA3, không khẳng định PA2 đã sửa mọi chỗ ảnh tùy chọn |
| [UC-13][uc13] | private.school_requests/campuses, domain uniqueness và role lf_catalog | T27; chưa chạy gửi email/duyệt trường qua HTTP |
| [OOD 4.3][ood-spec] | sessions, notifications và integration_tasks; cùng TxContext và task thử lại cho ngoại hệ | T13, T16, T30; chưa kiểm thử provider/worker tích hợp |

## OOD–ERD mapping

| OOD | Quan hệ dữ liệu / kiểm tra |
| --- | --- |
| User / AuthService | app.users + private.user_contacts, domains, sessions; email/verification là replica có nguồn Auth, không lưu password/token |
| University / Campus / ItemCategory | universities → campuses/domains; categories; Post chỉ lưu campus_id/category_id, không sao chép tên hoặc university_id suy ra |
| Post / LostPost / FoundPost | posts.post_type + subtype CHECK; private.post_details chứa private identifier/storage location; state CHECK và trigger theo 4.2/4.5 |
| ItemMedia | post_images một dòng mỗi ảnh; proof của Claim tối đa một tuple metadata; không lưu signed URL |
| Claim / ClaimService | claims.post_id + claimant_id, partial unique indexes, guard theo loại bài, decide_claim; bulk reject/cancel giữ lịch sử và xác định đúng recipient |
| ContactAccessService | read_post_contact/read_claimant_contact; chỉ đúng hai bên và đúng Claim ACCEPTED; chủ bài đọc liên hệ của chính mình; không có quyền riêng cho Admin |
| ModerationService / Report | reports + moderation_actions; UNIQUE reporter, trạng thái handled, snapshot trước REPORTED, audit append-only |
| CatalogService / SchoolRequest | private.school_requests và school_request_campuses; domain UQ; kết quả/đại diện không công khai |
| NotificationService | notifications lưu cùng transaction, read_at thay cho isRead/unreadCount dư; event/message code không chứa contact payload |
| Adapters / UnitOfWork | integration_tasks lưu thử lại; external object_key không phải FK giả tới Storage; không coi rollback PostgreSQL là rollback Auth/Storage |

**Components:** section 3 vẫn là template. Review này xác nhận ánh xạ OOD–ERD
và SQL, chưa xác nhận Component Diagram hoặc integration runtime đã được duyệt.

## Kết quả thực thi

Nguồn máy đọc được: [verification-results.json][results]. Tái chạy theo
[README][readme] bằng dependency đã pin trong [package-lock.json][lock].

Engine báo cáo: `PostgreSQL 18.6 (PGlite 0.5.16) on wasm32-unknown-emscripten, compiled by emcc (Emscripten gcc/clang-like replacement + linker emulating GNU ld) 6.0.13 (e13ee988ce3d87a738dd8f3661d02223308c412a), 32-bit`.

**32 passed, 0 failed.**

| ID | Kiểm tra thực thi | Kết quả |
| --- | --- | --- |
| T01 | 17 tables / 126 columns / 27 foreign keys materialise | PASS |
| T02 | NOT NULL and foreign keys reject invalid session | PASS |
| T03 | Case-insensitive category uniqueness | PASS |
| T04 | BR-01: unverified and banned users cannot create posts | PASS |
| T05 | Deferred one-contact and minimum-one-image constraints | PASS |
| T06 | Image slot, MIME, size checks and maximum five images | PASS |
| T07 | FOUND requires question and answer; answer alone is sufficient | PASS |
| T08 | LOST accepts message OR image, rejects neither | PASS |
| T09 | Reject self / unverified / banned Claimants | PASS |
| T10 | One PENDING per Post/User, resend after REJECTED allowed | PASS |
| T11 | Only owner decides; null decision is rejected | PASS |
| T12 | BR-02: Guest/student/PENDING/Admin cannot read foreign contact | PASS |
| T13 | ACCEPT atomically resolves Post, rejects others and opens both contacts | PASS |
| T14 | Partial UNIQUE prevents two ACCEPTED even before Post update | PASS |
| T15 | Deferred invariant rejects accepting without resolving/rejecting others | PASS |
| T16 | Injected error rolls back Claim, Post and notification | PASS |
| T17 | Manual resolution does not grant contact access | PASS |
| T18 | Question locked when pending Claim exists | PASS |
| T19 | BR-03: third DISTINCT reporter hides Post; duplicate cannot inflate count | PASS |
| T20 | KEEP restores previous state; handled reports do not re-hide | PASS |
| T21 | KEEP preserves RESOLVED and accepted contact rights | PASS |
| T22 | REMOVE requires Admin and reason; cancels pending and preserves audit | PASS |
| T23 | Public projection has no protected columns | PASS |
| T24 | anon/authenticated cannot bypass API via schema or RPC | PASS |
| T25 | Backend API cannot SELECT private contacts; auth column grant excludes phone | PASS |
| T26 | Soft deletion/history: API has no DELETE and audit cannot be edited | PASS |
| T27 | Pending school-domain uniqueness; catalog role does not read user contacts | PASS |
| T28 | All explicit indexes exist; all app tables have RLS | PASS |
| T29 | RESOLVED cannot be owner-deleted or edited | PASS |
| T30 | Owner ban hides existing posts and closes foreign contact access without changing Post state | PASS |
| T31 | Owner-feed query can use its intended index (planner capability, not benchmark) | PASS |
| T32 | Deliberate context replicas reject mismatched Claim/Post, event code and report audit | PASS |

## Giới hạn và yêu cầu triển khai

- auth.users và hai role browser chỉ là fixture của test; không kiểm tra OTP/link,
  SMTP, Storage ACL, MIME bytes hoặc Supabase deployment thật.
- RLS ở đây chỉ cho backend role; actor UUID truyền vào hàm **không xác thực người
  dùng cuối**. API phải lấy identity từ JWT đã kiểm tra, phân quyền từng endpoint
  và không cho client gọi trực tiếp các hàm với UUID tự chọn.
- Không chạy nhiều kết nối cạnh tranh, HTTP API, k6 100 người dùng/P95 hay uptime.
  T31 chỉ cho thấy planner có thể dùng index owner-feed khi tắt sequential scan,
  không phải benchmark hoặc bằng chứng hiệu năng production.
- SQL tham chiếu cần review quyền role/migration owner trước khi áp dụng lên môi
  trường hosting cụ thể; test không kết nối hoặc thay đổi CSDL thật của nhóm.

## Tài liệu cơ chế

- [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [Partial indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
- [SECURITY DEFINER](https://www.postgresql.org/docs/current/sql-createfunction.html)
- [PGlite](https://pglite.dev/docs/)

[erd]: ../../../pa/PA3/src_latex/sections/05-data-design/05.1-erd.tex
[relationships]: ../../../pa/PA3/src_latex/sections/05-data-design/05.1-relationships.tex
[dbml]: erd.dbml
[specs]: ../../../pa/PA3/src_latex/sections/05-data-design/05.2-table-specifications.tex
[schema]: schema.sql
[rules]: rules.sql
[review]: ../../../pa/PA3/src_latex/sections/05-data-design/05.3-normalisation-review.tex
[indexes]: ../../../pa/PA3/src_latex/sections/05-data-design/05.3-indexes.tex
[results]: verification-results.json
[readme]: README.md
[lock]: package-lock.json
[br]: ../../../pa/PA2/src_latex/sections/05-requirements/5.3-domain-requirements-and-business-rules.tex
[nfr]: ../../../pa/PA2/src_latex/sections/05-requirements/5.2-non-functional-requirements.tex
[uc05]: ../../../pa/PA2/src_latex/sections/07-use-case-specifications/7.5-use-case-uc-05.tex
[uc06]: ../../../pa/PA2/src_latex/sections/07-use-case-specifications/7.6-use-case-uc-06.tex
[uc07]: ../../../pa/PA2/src_latex/sections/07-use-case-specifications/7.7-use-case-uc-07.tex
[uc08]: ../../../pa/PA2/src_latex/sections/07-use-case-specifications/7.8-use-case-uc-08.tex
[uc13]: ../../../pa/PA2/src_latex/sections/07-use-case-specifications/7.13-use-case-uc-13.tex
[overview]: ../../../pa/PA3/src_latex/sections/02-design-overview/02-design-overview.tex
[ood]: ../../../pa/PA3/src_latex/sections/04-object-oriented-design/04.2-class-diagram.tex
[ood-spec]: ../../../pa/PA3/src_latex/sections/04-object-oriented-design/04.3-class-specifications.tex
