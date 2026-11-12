# PA3 OOD — Truy vết và bằng chứng kiểm tra

Ngày: 12/11/2026. Phạm vi: PA3 section 4.2–4.6.

## Checklist

| Yêu cầu | Bằng chứng | Trạng thái |
| --- | --- | --- |
| 4.2 UML ở mức thiết kế, có quan hệ và operation | [Class diagrams][classes]: domain, services, ports, adapters, catalog/search | Có |
| 4.3 Đặc tả 6–8 lớp quan trọng | [8 lớp C1–C8][specs], mỗi lớp có trách nhiệm, thuộc tính, operation và hợp đồng | Có |
| 4.4 Có 3–5 sequence diagram, ít nhất một alt | [5 hình cho UC-05/07/08/09/10][sequences]; UC-08/UC-10 gộp phần đọc và quyết định trong cùng hình | Có |
| 4.5 State machine cho Post/Claim | [Post, Claim và User][states], có điều kiện chuyển và tác động | Có |
| 4.6 Principles/patterns: where/why | [Bảng nguyên tắc và vị trí áp dụng][patterns] | Có |
| Message tương ứng operation của class diagram | Đối chiếu lời gọi trong 5 file sequence bên dưới với các operation ở 4.2; kiểm tra tĩnh tên operation và target lifeline | Có; chưa phải kiểm thử ứng dụng |
| Review với components | [Section 3][architecture] hiện chưa có Component Diagram hay danh sách component đã chốt | **Chưa đủ đầu vào để xác nhận** |
| Review với ERD | [Section 5][data] hiện chưa có ERD, bảng hay ràng buộc dữ liệu cụ thể | **Chưa đủ đầu vào để xác nhận** |
| Liên kết diagram và evidence | Các liên kết nguồn dưới đây, tham chiếu Figure trong PDF, [PDF đã build][pdf] | Có |

## Sơ đồ sequence và nguồn nghiệp vụ

| Use case | Sơ đồ | Nguồn đối chiếu |
| --- | --- | --- |
| UC-05 — Tạo bài | [sequence-uc05.tex][seq05] | [UC-05 PA2][uc05], section 2 và 4.1 PA3 |
| UC-07 — Gửi Claim | [sequence-uc07.tex][seq07] | [UC-07 PA2][uc07]; FoundPost cần câu trả lời, LostPost cần mô tả hoặc ảnh |
| UC-08 — Xem và quyết định Claim | [sequence-uc08.tex][seq08] | [UC-08 PA2][uc08]; quyền chủ bài, ACCEPT/REJECT, trạng thái và liên hệ hai bên |
| UC-09 — Báo cáo | [sequence-uc09.tex][seq09] | [UC-09 PA2][uc09] và [section 2 PA3][overview]; quyết định tự động ẩn theo PA3 |
| UC-10 — Kiểm duyệt | [sequence-uc10.tex][seq10] | [UC-10 PA2][uc10]; đọc hàng đợi, giữ/gỡ, audit; khóa tài khoản được đặc tả bằng operation và diễn giải |

## Đầu mục cần đối chiếu khi có components và ERD

Đây là **danh sách đối chiếu dự kiến**, không phải component hoặc schema đã được nhóm phê duyệt. Chưa gán CMP-ID hoặc tên bảng để tránh tạo bằng chứng không tồn tại.

| Nhóm nghiệp vụ theo section 2 | Lớp/interface OOD | Nội dung cần section 3/5 xác nhận |
| --- | --- | --- |
| Xác thực và tài khoản | User, AuthService, IAuthProvider, IUserRepository | Component sở hữu Auth/profile; quan hệ auth identity–User, xác minh, khóa đăng nhập và thu hồi phiên |
| Bài đăng và tìm kiếm | Post/subtypes, ItemMedia, PostService, SearchService | Component truy cập Post/Storage; Post–User–Campus–Category; ảnh 1–5 theo 4.1; CLOSED/REPORTED và previousStatus |
| Claim | Claim, ClaimService, IClaimRepository | FK tới Post chung; một PENDING/Post/User, một ACCEPTED/Post; transaction duyệt và tập Claim được thông báo |
| Liên hệ riêng | ContactDetails, ContactAccessService, IContactRepository | Quyền đọc và nơi lưu liên hệ; cùng snapshot; dữ liệu riêng không vào projection công khai |
| Kiểm duyệt | Report, ModerationService, IReportRepository | Một report/Post/User; ngưỡng 3 người chưa xử lý; khôi phục bài, hủy Claim và audit |
| Danh mục/trường | University, Campus, SchoolRequest, CatalogService | Quan hệ trường–cơ sở–tên miền; duyệt yêu cầu nguyên tử; ẩn danh mục vẫn giữ tham chiếu bài cũ |
| Thông báo | NotificationService, INotificationRepository | Component gửi/lưu thông báo; cùng transaction với thay đổi trạng thái và chỉ đúng người nhận |

Khi section 3 và 5 có nội dung, cần bổ sung mã component, bảng/FK/index thực tế và kết quả đối chiếu từng dòng. Hiện chỉ có thể xác nhận nội dung OOD và tính nhất quán nội bộ, **chưa xác nhận hoàn tất review components/ERD**.

[classes]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/04.2-class-diagram.tex
[specs]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/04.3-class-specifications.tex
[sequences]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/04.4-sequence-diagrams.tex
[states]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/04.5-state-machines.tex
[patterns]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/04.6-design-principles.tex
[architecture]: ../../pa/PA3/src_latex/sections/03-architectural-design/03-architectural-design.tex
[data]: ../../pa/PA3/src_latex/sections/05-data-design/05-data-design.tex
[overview]: ../../pa/PA3/src_latex/sections/02-design-overview/02-design-overview.tex
[pdf]: ../../pa/PA3/src_latex/main.pdf
[seq05]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/sequence-uc05.tex
[seq07]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/sequence-uc07.tex
[seq08]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/sequence-uc08.tex
[seq09]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/sequence-uc09.tex
[seq10]: ../../pa/PA3/src_latex/sections/04-object-oriented-design/sequence-uc10.tex
[uc05]: ../../pa/PA2/src_latex/sections/07-use-case-specifications/7.5-use-case-uc-05.tex
[uc07]: ../../pa/PA2/src_latex/sections/07-use-case-specifications/7.7-use-case-uc-07.tex
[uc08]: ../../pa/PA2/src_latex/sections/07-use-case-specifications/7.8-use-case-uc-08.tex
[uc09]: ../../pa/PA2/src_latex/sections/07-use-case-specifications/7.9-use-case-uc-09.tex
[uc10]: ../../pa/PA2/src_latex/sections/07-use-case-specifications/7.10-use-case-uc-10.tex
