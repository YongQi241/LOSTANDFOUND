# ADR-003: Xác thực bằng Supabase Auth, mọi thao tác đi qua API

- Status: Accepted
- Date: 2026-11-11
- Deciders: Designer/Architect, Developer

## Context
- FR-01, BR-01: chỉ đăng ký bằng email của trường đã có trong hệ thống.
- UC-01: link xác minh hạn 24 giờ.
- UC-02 E4: khóa đăng nhập 15 phút sau 5 lần sai.
- UC-10 A2: khóa tài khoản phải kết thúc phiên ngay.
- SPA và API ở hai tên miền khác nhau.

## Decision
Supabase Auth lưu mật khẩu đã băm, gửi link xác minh qua SMTP của Brevo và cấp JWT.
Mọi thao tác xác thực đi qua CMP-01:
- API kiểm tra tên miền trước khi gọi Auth tạo tài khoản.
- API đếm số lần đăng nhập sai trong CSDL.
- SPA gửi access token qua header Authorization (không dùng cookie).
- Middleware kiểm tra chữ ký JWT, rồi đọc vai trò và trạng thái tài khoản từ CSDL ở mỗi request.

## Alternatives considered
1. Tự viết bằng bcrypt, jsonwebtoken và bảng token: nhiều code, dễ sai sót bảo mật.
2. Firebase Auth / Auth0: thêm một nhà cung cấp, cấu hình SMTP riêng.
3. SPA gọi thẳng Supabase Auth: không chặn được tên miền, không đếm được lần sai theo UC-02 E4.

## Consequences
- Tích cực: không tự viết phần lưu mật khẩu và gửi link xác minh; khóa tài khoản có hiệu lực ngay.
- Tiêu cực: mỗi request tốn thêm một lần đọc CSDL; cấu hình Auth (redirect URL, thời hạn link, SMTP) phải ghi trong README.