# BÀN GIAO MÔ HÌNH THỰC THỂ MIỀN NGHIỆP VỤ (DOMAIN ENTITIES HANDOVER)
**Dự án:** US-Recovery (CampusHub) — Hệ thống Quản trị & Tìm kiếm Đồ thất lạc Đại học  
**Giai đoạn:** Software Design (PA3)  
**Người thực hiện (BA):** Huỳnh Thái Hòa (MSSV: 24127374)  
**Người nhận bàn giao:**
* **Designer / Architect (Des):** Nguyễn Anh Tá (MSSV: 24127117) — Phục vụ thực hiện Section 4.2 (Class Diagram), 4.3 (Class Specifications), 4.4 (Sequence Diagrams), 4.5 (State Machine Diagrams) và Section 6 (UI/UX Design).
* **Developer (Dev):** Nguyễn Gia (MSSV: 24127357) — Phục vụ thực hiện Section 5 (Data Design: ERD, Bảng dữ liệu CSDL PostgreSQL trên Supabase, Chuẩn hóa 3NF và Indexes) và hiện thực mã nguồn Backend API.

---

## 1. Mục đích bàn giao

Tài liệu này tổng hợp toàn bộ các thực thể khái niệm (Conceptual Domain Entities), thuộc tính cốt lõi, mối quan hệ và cơ chế bảo đảm 4 quy tắc nghiệp vụ then chốt đã hoàn thiện trong **Section 2.1** và **Section 4.1** của báo cáo PA3. Đây là cơ sở bất biến để Đội ngũ Thiết kế (Designer) và Phát triển (Developer) tiến hành phân rã chi tiết mà không bị sai lệch nghiệp vụ.

---

## 2. Danh sách 10 Thực thể Nghiệp vụ được Phê duyệt (Approved Domain Entities)

| STT | Tên thực thể | Bản chất nghiệp vụ | Các thuộc tính khái niệm chính (No Methods) | Quy tắc nghiệp vụ liên quan |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `User` | Đại diện cho sinh viên đại học hoặc quản trị viên hệ thống. | `userId`, `fullName`, `universityEmail`, `phoneNumber`, `studentId`, `role` (GUEST, STUDENT, ADMIN), `status` (ACTIVE, BANNED) | **BR-01:** Phải có email trường `@...edu.vn` đã xác thực.<br>**BR-02:** SĐT được che giấu mặc định. |
| **2** | `UniversityCampus` | Cơ sở trường đại học nơi xảy ra sự việc (CS1 Nguyễn Văn Cừ, CS2 Linh Trung,...). | `campusId`, `campusName`, `campusCode`, `address`, `status` (APPROVED, PENDING) | Cơ sở mới cần Admin phê duyệt (**FR-08**). |
| **3** | `ItemCategory` | Danh mục phân loại vật phẩm (Thẻ SV, Điện tử, Ví/Bóp, Chìa khóa, Balo,...). | `categoryId`, `categoryName`, `description` | Phục vụ bộ lọc đa chiều (**FR-04**). |
| **4** | `Post` *(Abstract)* | Thực thể chung cho tin báo cáo mất đồ hoặc nhặt được đồ. | `postId`, `title`, `description`, `incidentDate`, `locationDetail`, `status` (ACTIVE, PENDING_VERIFICATION, RESOLVED, CLOSED, REPORTED), `createdAt` | **BR-03:** Tự động chuyển vào hàng đợi nếu $\ge 3$ báo cáo vi phạm. |
| **5** | `LostPost` | Chuyên biệt hóa của `Post` cho trường hợp sinh viên tìm đồ bị thất lạc. | Kế thừa `Post`, bổ sung: `rewardAmount` (khoản hậu tạ), `privateIdentifier` (đặc điểm nhận dạng kín). | Chỉ chủ bài đăng mới được chuyển trạng thái sang `RESOLVED`. |
| **6** | `FoundPost` | Chuyên biệt hóa của `Post` cho trường hợp nhặt được tài sản và tìm chủ. | Kế thừa `Post`, bổ sung: `storageLocation` (nơi giữ đồ), `securityQuestion` (câu hỏi bảo mật). | **BR-04:** Chứa câu hỏi xác minh làm cơ sở đối chiếu Claim. |
| **7** | `ItemMedia` | Tệp hình ảnh minh chứng vật phẩm thất lạc hoặc khu vực xảy ra. | `mediaId`, `mediaUrl`, `fileType`, `uploadedAt` | Mỗi bài đăng chứa ít nhất 1 ảnh ($1..\ast$). Tự động làm mờ nếu là thẻ SV (**FR-10**). |
| **8** | `Claim` | Yêu cầu nhận lại tài sản do sinh viên gửi đến bài nhặt đồ. | `claimId`, `claimMessage`, `proofImage`, `securityAnswer`, `status` (PENDING, ACCEPTED, REJECTED, CANCELLED), `submittedAt` | **BR-04:** Vòng đời xác minh 2 bước (Pending $\rightarrow$ Accepted / Rejected). |
| **9** | `Report` | Phản ánh bài đăng sai sự thật, gian lận, spam hoặc nội dung không hợp lệ. | `reportId`, `reason`, `detailMessage`, `status` (PENDING, APPROVED, DISMISSED), `reportedAt` | **BR-03:** Đạt ngưỡng $\ge 3$ báo cáo thì hệ thống tự động ẩn bài. |
| **10** | `Notification` | Thông báo đẩy trong ứng dụng gửi đến người dùng. | `notificationId`, `title`, `messageBody`, `type`, `isRead`, `createdAt` | Tự động phát khi có Claim mới hoặc đổi trạng thái bài đăng (**FR-09**). |

---

## 3. Ma trận Quan hệ và Bội số (Relationships & Multiplicities)

* `UniversityCampus` **1 : 0..*** `Post` *(hosts / located_at)*
* `ItemCategory` **1 : 0..*** `Post` *(classifies)*
* `Post` **1 : 1..*** `ItemMedia` *(contains)*
* `User` **1 : 0..*** `Post` *(creates / owns)*
* `Post` **1 : 1** `LostPost / FoundPost` *(generalizes)*
* `FoundPost` **1 : 0..*** `Claim` *(receives)*
* `User` **1 : 0..*** `Claim` *(submits)*
* `Post` **1 : 0..*** `Report` *(flagged_on)*
* `User` **1 : 0..*** `Report` *(files)*
* `User` **1 : 0..*** `Notification` *(receives)*

---

## 4. Xác minh và Chỉ dẫn Hiện thực 4 Quy tắc Nghiệp vụ Cốt lõi

### 4.1. Quy tắc 1: Xác thực Email trường (BR-01 — Verified School Email)
* **Ý nghĩa:** Chỉ những tài khoản đã kích hoạt qua email `@...edu.vn` mới được phép tạo `Post` hoặc gửi `Claim`. Khách (*Guest*) chỉ có quyền xem và tìm kiếm tin (*Read-only*).
* **Chỉ dẫn cho Des:** Trên Class Diagram (4.2), gán phương thức kiểm tra quyền hạn `canPost()` / `canClaim()` trên `UserService` hoặc `AuthGuard`.
* **Chỉ dẫn cho Dev:** Trên CSDL Supabase, kiểm tra trường `is_verified = TRUE` hoặc gán Row Level Security (RLS) để chặn thao tác INSERT vào bảng `posts` và `claims`.

### 4.2. Quy tắc 2: Bảo vệ Thông tin Liên hệ (BR-02 — Protected Contact Details)
* **Ý nghĩa:** Số điện thoại và email cá nhân của chủ bài đăng không được trả về trong các API công khai; chỉ được mở khóa cho `Claimant` khi `Claim.status == 'ACCEPTED'`.
* **Chỉ dẫn cho Des:** Thiết kế Sequence Diagram (4.4) thể hiện rõ luồng trả lời API có bước lọc dữ liệu (*Data Masking*).
* **Chỉ dẫn cho Dev:** Tại tầng Business Service của Express.js, không đính kèm `phoneNumber` trong DTO trả về cho chi tiết bài đăng, trừ khi `currentUserId == post.authorId` hoặc tồn tại Claim của `currentUserId` có trạng thái `ACCEPTED`.

### 4.3. Quy tắc 3: Quy trình Phê duyệt Claim (BR-04 — Claim Approval Workflow)
* **Ý nghĩa:** Người nhặt đối chiếu câu trả lời bí mật (`securityAnswer`) và hình ảnh chứng minh (`proofImage`) để duyệt (*Accepted*) hoặc từ chối (*Rejected*). Khi duyệt thành công:
  * `Claim.status` $\rightarrow$ `ACCEPTED`.
  * `Post.status` $\rightarrow$ `RESOLVED`.
  * Hệ thống phát sinh `Notification` thông báo cho Claimant và mở khóa thông tin liên hệ.
* **Chỉ dẫn cho Des:** Vẽ State Machine Diagram (4.5) cho `Claim` và `Post`.
* **Chỉ dẫn cho Dev:** Sử dụng Database Transaction trong PostgreSQL để cập nhật đồng thời bảng `claims` và bảng `posts`, tránh tình trạng bất đồng bộ dữ liệu.

### 4.4. Quy tắc 4: Ngưỡng Tự động Kiểm duyệt (BR-03 — Moderation Threshold)
* **Ý nghĩa:** Khi một bài đăng nhận từ 3 lượt báo cáo từ các người dùng khác nhau ($\ge 3$ reports):
  * `Post.status` $\rightarrow$ `REPORTED` (tự động ẩn khỏi trang tìm kiếm công khai).
  * Bài đăng được chuyển thẳng vào Hàng đợi Kiểm duyệt (*Moderation Queue*) của Admin.
* **Chỉ dẫn cho Des:** Thể hiện trạng thái `REPORTED` trong State Machine Diagram của `Post`.
* **Chỉ dẫn cho Dev:** Tạo Database Trigger hoặc hàm kiểm tra tại `ReportService`: sau khi thêm mới một `Report`, thực hiện đếm số report của bài; nếu $\ge 3$, tự động cập nhật `posts.status = 'REPORTED'`.

---

*Mọi thắc mắc hoặc đề xuất điều chỉnh chi tiết cài đặt, vui lòng phản hồi qua kênh trao đổi nhóm hoặc issue trên GitHub.*
