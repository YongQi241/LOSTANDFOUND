# ADR-002: PostgreSQL trên Supabase, ảnh lưu ở Supabase Storage

- Status: Accepted
- Date: 2026-11-11
- Deciders: Designer/Architect, Developer

## Context
Dữ liệu có quan hệ rõ ràng (tài khoản, bài đăng, Claim, báo cáo, danh mục, trường).
Cần các ràng buộc chặt:
- Mỗi người chỉ có một Claim đang chờ trên một bài.
- Mỗi người chỉ báo cáo một bài một lần.
- BR-03 đếm số người báo cáo khác nhau.

Chấp nhận Claim và gỡ bài đổi nhiều bản ghi cùng lúc. Ngân sách hosting gần bằng 0.

## Decision
- PostgreSQL do Supabase quản lý, vùng Singapore.
- API truy cập bằng `pg` qua connection pooler; dùng transaction cho thao tác đổi nhiều bản ghi.
- Ràng buộc giữ bằng khóa ngoại, UNIQUE, CHECK (chi tiết ở Section 5).
- Ảnh lưu ở Supabase Storage: bucket `post-images` đọc công khai, `claim-evidence` riêng tư (signed URL).

## Alternatives considered
1. MongoDB Atlas: ràng buộc giữa nhiều collection và truy vấn kết hợp yếu hơn.
2. PostgreSQL/MySQL tự cài trên VPS: tốn phí, tự lo sao lưu và bảo mật.
3. Firebase Firestore: giới hạn khi lọc nhiều điều kiện, không hợp với UC-03.

## Consequences
- Tích cực: CSDL tự chặn dữ liệu sai; một nhà cung cấp cho CSDL, Auth, Storage.
- Tiêu cực: phụ thuộc giới hạn gói miễn phí (xem ADR-004); gắn với Supabase cho Auth và Storage. Rủi ro này được giảm nhờ CMP-12 Adapters.