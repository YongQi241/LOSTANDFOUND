# ADR-001: API modular monolith là cổng duy nhất vào dữ liệu

- Status: Accepted
- Date: 2026-11-11
- Deciders: Designer/Architect, Developer

## Context
NFR-02 không cho phép thông tin liên hệ xuất hiện trong response gửi cho người chưa được phép.
BR-01 đến BR-03 và luồng Claim cần được kiểm thử tự động bằng Jest và Supertest.
Nhóm có 5 người, tối đa 3 tuần coding.

## Decision
SPA chỉ gọi REST API (Express.js), không truy cập trực tiếp CSDL hay Supabase Auth.
Ngoại lệ duy nhất là đọc ảnh bằng URL do API cấp.
API là một ứng dụng duy nhất, chia thành các module CMP-01 đến CMP-09.
Mỗi module chia lớp controller, service, repository.

## Alternatives considered
1. SPA gọi thẳng Supabase, bảo vệ bằng Row Level Security: quy tắc nằm trong policy SQL, khó kiểm thử, khó ẩn đúng một cột theo từng người xem.
2. Microservices: chi phí deploy và giám sát lớn; không có transaction xuyên service.
3. Hàm serverless (Vercel Functions, Supabase Edge Functions): khởi động lạnh theo từng hàm, khó chạy thử đầy đủ trên máy cá nhân.

## Consequences
- Tích cực: kiểm tra quyền tập trung một nơi, dễ review và kiểm thử; có thể đổi CSDL mà không sửa SPA.
- Tiêu cực: phải viết nhiều endpoint hơn; mọi request đi qua một instance API (xem ADR-004).