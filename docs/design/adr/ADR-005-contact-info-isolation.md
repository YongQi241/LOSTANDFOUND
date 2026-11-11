# ADR-005: Thông tin liên hệ lưu riêng, chỉ trả qua một endpoint có kiểm tra quyền

- Status: Accepted
- Date: 2026-11-11
- Deciders: Designer/Architect, Developer, Tester

## Context
- BR-02, NFR-02: liên hệ chỉ mở cho hai bên khi Claim được chấp nhận; kiểm tra bằng Postman với 3 loại tài khoản.
- Từ PA3, ô liên hệ là bắt buộc trong form đăng bài.
- Chỉ ẩn trên giao diện thì vẫn đọc được bằng công cụ của trình duyệt.

## Decision
- Thông tin liên hệ lưu ở bảng riêng, quan hệ 1-1 với bài đăng. Chỉ repository của CMP-05 được đọc bảng này.
- GET /posts và GET /posts/:id không bao giờ chứa liên hệ.
- GET /posts/:id/contact chỉ trả cho chủ bài hoặc Claimant đã được chấp nhận; trường hợp khác trả lỗi 403.
- GET /claims/:id/contact trả liên hệ của Claimant cho chủ bài sau khi chấp nhận.
- Response được dựng theo danh sách trường cho phép.
- Test tích hợp kiểm tra các endpoint tìm kiếm, chi tiết và Claim không chứa liên hệ với cả 3 loại tài khoản.

## Alternatives considered
1. Để chung bảng bài đăng và bỏ cột trong từng truy vấn: viết sót một câu là lộ dữ liệu.
2. Chỉ ẩn trên giao diện: vi phạm NFR-02.
3. Phân quyền theo cột trong PostgreSQL: API dùng một tài khoản CSDL nên không phân biệt được người xem.
4. Mã hóa trường liên hệ: thêm quản lý khóa, không giải quyết câu hỏi ai được xem.

## Consequences
- Tích cực: muốn lộ liên hệ phải viết code cố ý qua CMP-05; dễ review và kiểm thử.
- Tiêu cực: SPA tốn thêm một request khi liên hệ đã mở; Section 5 phải thể hiện bảng mới.