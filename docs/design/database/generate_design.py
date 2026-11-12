"""Generate SQL, the LaTeX dictionary/indexes and DBML from one reviewed model.

Run from any directory: python docs/design/database/generate_design.py
Custom integrity/privacy SQL is maintained in rules.sql, not generated here.
"""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT = ROOT / 'pa/PA3/src_latex/sections/05-data-design'
TABLES = []

def col(name, typ, description, *, null=False, default=None, pk=False, ref=None, unique=False, check=None):
    return dict(name=name, type=typ, description=description, null=null, default=default,
                pk=pk, ref=ref, unique=unique, check=check)

def table(name, description, columns, constraints=()):
    TABLES.append(dict(name=name, description=description, columns=columns, constraints=list(constraints)))

def uid(name, description, ref=None, pk=False, null=False):
    return col(name, 'uuid', description, pk=pk, ref=ref, null=null,
               default='gen_random_uuid()' if pk and not ref else None)

def stamp(name='created_at', description='Thời điểm tạo, lưu UTC.'):
    return col(name, 'timestamptz', description, default='CURRENT_TIMESTAMP')

table('app.universities', 'Trường đại học tham gia; yêu cầu chưa duyệt nằm ở bảng riêng.', [
    uid('university_id','Định danh trường.',pk=True),
    col('code','varchar(30)','Mã trường chuẩn hóa.',unique=True,check="code = upper(btrim(code)) AND code <> ''"),
    col('name','varchar(200)','Tên trường.',check="btrim(name) <> ''"),
    col('status','varchar(12)','Trạng thái trường.',default="'APPROVED'",check="status IN ('PENDING','APPROVED')"),stamp()])
table('app.university_domains','Tên miền được phép đăng ký; một trường có thể có nhiều tên miền.',[
    col('domain','varchar(253)','Tên miền chính xác, chữ thường, không có @.',pk=True,check="domain = lower(domain) AND domain ~ '^[a-z0-9][a-z0-9.-]*[.]edu[.]vn$'"),
    uid('university_id','Trường sở hữu tên miền.',ref='app.universities.university_id')])
table('app.campuses','Cơ sở của trường dùng để đăng bài và lọc.',[
    uid('campus_id','Định danh cơ sở.',pk=True),uid('university_id','Trường sở hữu.',ref='app.universities.university_id'),
    col('name','varchar(150)','Tên cơ sở.',check="btrim(name) <> ''"),col('address','text','Địa chỉ cơ sở.',check="btrim(address) <> ''"),
    col('is_active','boolean','Còn được chọn cho bài mới.',default='true')])
table('app.categories','Danh mục vật phẩm; ẩn danh mục không xóa tham chiếu bài cũ.',[
    uid('category_id','Định danh danh mục.',pk=True),col('name','varchar(100)','Tên danh mục.',check="btrim(name) <> ''"),
    col('is_active','boolean','Danh mục được hiển thị trong form.',default='true')])
table('app.users','Profile nghiệp vụ; mật khẩu và link xác minh thuộc Supabase Auth.',[
    uid('user_id','Cùng UUID với auth.users; không tự sinh identity thứ hai.',pk=True,ref='auth.users.id'),
    col('full_name','varchar(150)','Họ tên.',check="btrim(full_name) <> ''"),
    col('role','varchar(10)','Vai trò lưu trong CSDL; Guest không có bản ghi.',default="'STUDENT'",check="role IN ('STUDENT','ADMIN')"),
    col('status','varchar(10)','Trạng thái tài khoản.',default="'ACTIVE'",check="status IN ('ACTIVE','BANNED')"),
    col('is_verified','boolean','Bản đồng bộ kết quả xác minh đáng tin cậy.',default='false'),
    col('student_id','varchar(30)','MSSV tùy chọn, không có trong projection công khai.',null=True),
    col('failed_login_count','smallint','Số lần sai liên tiếp.',default='0',check='failed_login_count BETWEEN 0 AND 5'),
    col('login_locked_until','timestamptz','Khóa đăng nhập tạm thời 15 phút; khác BANNED.',null=True),
    col('ban_reason','text','Lý do khóa bởi Admin.',null=True),stamp()], [
    ('users_ban_reason',"CHECK (status <> 'BANNED' OR nullif(btrim(ban_reason),'') IS NOT NULL)")])
table('private.user_contacts','Email trường và số điện thoại được bảo vệ; không join vào kết quả công khai.',[
    uid('user_id','Mỗi profile có đúng một bản ghi liên hệ.',pk=True,ref='app.users.user_id'),
    col('university_email','varchar(254)','Email trường chuẩn hóa; nguồn liên hệ Claimant sau ACCEPT.',unique=True,
        check="university_email = lower(btrim(university_email)) AND university_email ~ '^[^@[:space:]]+@[^@[:space:]]+$'"),
    col('email_domain','varchar(253)','Tên miền trường đã đăng ký.',ref='app.university_domains.domain'),
    col('phone_number','varchar(10)','Số điện thoại nếu có.',null=True,check="phone_number ~ '^[0-9]{10}$'")], [
    ('user_contact_domain',"CHECK (split_part(university_email,'@',2) = email_domain)")])
table('app.sessions','Định danh phiên để kiểm tra thu hồi; không lưu access/refresh token.',[
    col('session_id','uuid','Session ID từ Auth adapter, không sinh ID không khớp token.',pk=True),uid('user_id','Chủ phiên.',ref='app.users.user_id'),
    stamp(),col('expires_at','timestamptz','Hạn phiên/token đang theo dõi.'),
    col('revoked_at','timestamptz','Có giá trị khi logout hoặc khóa tài khoản.',null=True)], [
    ('sessions_time','CHECK (expires_at > created_at AND (revoked_at IS NULL OR revoked_at >= created_at))')])
table('app.posts','Single-table inheritance cho LostPost/FoundPost; dữ liệu riêng được tách.',[
    uid('post_id','Định danh bài.',pk=True),uid('owner_id','Chủ bài.',ref='app.users.user_id'),
    uid('campus_id','Cơ sở xảy ra sự việc.',ref='app.campuses.campus_id'),uid('category_id','Danh mục vật phẩm.',ref='app.categories.category_id'),
    col('post_type','varchar(5)','Loại bài, độc lập vòng đời.',check="post_type IN ('LOST','FOUND')"),
    col('title','varchar(200)','Tiêu đề tìm kiếm.',check="btrim(title) <> ''"),
    col('description','text','Mô tả tùy chọn.',null=True),col('location_detail','text','Vị trí chi tiết tùy chọn.',null=True),
    col('incident_at','timestamptz','Thời gian mất/nhặt, không được ở tương lai khi ghi.'),
    col('verification_question','text','Bắt buộc với FOUND, NULL với LOST.',null=True),
    col('reward_amount','numeric(12,2)','Hậu tạ tùy chọn của LOST.',null=True,check='reward_amount >= 0'),
    col('status','varchar(10)','Vòng đời theo OOD.',default="'ACTIVE'",check="status IN ('ACTIVE','RESOLVED','REPORTED','CLOSED')"),
    col('previous_status','varchar(10)','Chỉ có khi REPORTED để khôi phục đúng trạng thái.',null=True),
    col('close_reason','varchar(20)','OWNER_DELETED hoặc ADMIN_REMOVED.',null=True),
    col('closure_note','text','Lý do gỡ; không đưa vào kết quả công khai.',null=True),
    col('closed_at','timestamptz','Thời điểm đóng.',null=True),stamp(),stamp('updated_at','Thời điểm cập nhật.'),
    col('search_vector','tsvector','Projection tìm kiếm được tính từ nội dung công khai.',default="GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, title || ' ' || coalesce(description,'') || ' ' || coalesce(location_detail,''))) STORED")], [
    ('posts_subtype',"CHECK ((post_type = 'FOUND' AND nullif(btrim(verification_question),'') IS NOT NULL AND reward_amount IS NULL) OR (post_type = 'LOST' AND verification_question IS NULL))"),
    ('posts_previous',"CHECK ((status = 'REPORTED' AND previous_status IS NOT NULL AND previous_status IN ('ACTIVE','RESOLVED')) OR (status <> 'REPORTED' AND previous_status IS NULL))"),
    ('posts_closure',"CHECK ((status = 'CLOSED' AND close_reason IS NOT NULL AND close_reason IN ('OWNER_DELETED','ADMIN_REMOVED') AND closed_at IS NOT NULL AND (close_reason <> 'ADMIN_REMOVED' OR nullif(btrim(closure_note),'') IS NOT NULL)) OR (status <> 'CLOSED' AND close_reason IS NULL AND closed_at IS NULL AND closure_note IS NULL))")])
table('private.post_details','Liên hệ chủ bài theo từng Post và thuộc tính subtype riêng tư.',[
    uid('post_id','Đúng một bản ghi trên Post tại commit.',pk=True,ref='app.posts.post_id'),
    col('contact_kind','varchar(5)','Loại liên hệ.',check="contact_kind IN ('PHONE','EMAIL')"),
    col('contact_value','varchar(254)','Liên hệ hợp lệ, không nằm trong public_posts.'),
    col('private_identifier','text','Đặc điểm nhận dạng kín của LOST.',null=True),
    col('storage_location','text','Nơi giữ đồ của FOUND; không công khai.',null=True)], [
    ('post_contact_value',"CHECK ((contact_kind = 'PHONE' AND contact_value ~ '^[0-9]{10}$') OR (contact_kind = 'EMAIL' AND contact_value ~ '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'))")])
table('app.post_images','Metadata ảnh bài; binary nằm ở Supabase Storage.',[
    uid('image_id','Định danh ảnh.',pk=True),uid('post_id','Bài chứa ảnh.',ref='app.posts.post_id'),
    col('position','smallint','Vị trí gallery 1–5.',check='position BETWEEN 1 AND 5'),
    col('object_key','text','Object key trong post-images; không lưu signed URL.',unique=True,check="btrim(object_key) <> ''"),
    col('mime_type','varchar(10)','MIME đã kiểm tra từ nội dung file.',check="mime_type IN ('image/jpeg','image/png')"),
    col('size_bytes','integer','Dung lượng thực tế.',check='size_bytes BETWEEN 1 AND 5242880'),stamp()], [
    ('post_images_position','UNIQUE (post_id, position)')])
table('app.claims','Claim đến Post chung, hỗ trợ cả LOST và FOUND; câu trả lời/bằng chứng không công khai.',[
    uid('claim_id','Định danh Claim.',pk=True),uid('post_id','Bài nhận Claim.',ref='app.posts.post_id'),uid('claimant_id','Người gửi.',ref='app.users.user_id'),
    col('security_answer','text','Bắt buộc với bài FOUND.',null=True),col('claim_message','text','Mô tả nơi nhặt với LOST.',null=True),
    col('proof_object_key','text','Một ảnh trong claim-evidence riêng tư.',null=True,unique=True),
    col('proof_mime_type','varchar(10)','MIME của bằng chứng nếu có.',null=True),
    col('proof_size_bytes','integer','Dung lượng bằng chứng nếu có.',null=True),
    col('status','varchar(10)','Máy trạng thái Claim.',default="'PENDING'",check="status IN ('PENDING','ACCEPTED','REJECTED','CANCELLED')"),
    col('decision_reason','text','Lý do từ chối tùy chọn; hủy có mã nguyên nhân.',null=True),
    col('decided_at','timestamptz','Có khi không còn PENDING.',null=True),stamp('submitted_at','Thời điểm gửi.')], [
    ('claim_proof',"CHECK ((proof_object_key IS NULL AND proof_mime_type IS NULL AND proof_size_bytes IS NULL) OR (proof_object_key IS NOT NULL AND btrim(proof_object_key) <> '' AND proof_mime_type IS NOT NULL AND proof_mime_type IN ('image/jpeg','image/png') AND proof_size_bytes IS NOT NULL AND proof_size_bytes BETWEEN 1 AND 5242880))"),
    ('claim_decision',"CHECK ((status = 'PENDING' AND decided_at IS NULL AND decision_reason IS NULL) OR (status <> 'PENDING' AND decided_at IS NOT NULL AND decided_at >= submitted_at AND (status <> 'CANCELLED' OR nullif(btrim(decision_reason),'') IS NOT NULL)))")])
table('app.moderation_actions','Audit append-only cho giữ/gỡ bài và khóa tài khoản.',[
    uid('action_id','Định danh audit.',pk=True),uid('admin_id','Admin thực hiện.',ref='app.users.user_id'),
    uid('post_id','Đích là bài khi KEEP/REMOVE.',ref='app.posts.post_id',null=True),
    uid('target_user_id','Đích tài khoản khi BAN_USER.',ref='app.users.user_id',null=True),
    col('action','varchar(12)','Loại thao tác.',check="action IN ('KEEP_POST','REMOVE_POST','BAN_USER')"),
    col('reason','text','Lý do bắt buộc cho gỡ/khóa.',null=True),stamp()], [
    ('moderation_target',"CHECK ((action IN ('KEEP_POST','REMOVE_POST') AND post_id IS NOT NULL AND target_user_id IS NULL) OR (action = 'BAN_USER' AND target_user_id IS NOT NULL AND post_id IS NULL))"),
    ('moderation_reason',"CHECK (action = 'KEEP_POST' OR nullif(btrim(reason),'') IS NOT NULL)")])
table('app.reports','Mỗi người báo cáo một bài một lần, không xóa lịch sử khi Admin giữ bài.',[
    uid('report_id','Định danh báo cáo.',pk=True),uid('post_id','Bài bị báo cáo.',ref='app.posts.post_id'),uid('reporter_id','Người báo cáo.',ref='app.users.user_id'),
    col('reason','varchar(12)','Lý do báo cáo.',check="reason IN ('SPAM','FALSE_INFO','INAPPROPRIATE','OTHER')"),
    col('detail_message','text','OTHER bắt buộc có mô tả.',null=True),
    col('status','varchar(10)','Trạng thái xét báo cáo.',default="'PENDING'",check="status IN ('PENDING','APPROVED','DISMISSED')"),
    uid('action_id','Audit đã xử lý báo cáo.',ref='app.moderation_actions.action_id',null=True),stamp('reported_at','Thời điểm báo cáo.')], [
    ('report_once','UNIQUE (post_id, reporter_id)'),
    ('report_other',"CHECK (reason <> 'OTHER' OR nullif(btrim(detail_message),'') IS NOT NULL)"),
    ('report_settlement',"CHECK ((status = 'PENDING' AND action_id IS NULL) OR (status <> 'PENDING' AND action_id IS NOT NULL))")])
table('app.notifications','Thông báo in-app lưu cùng transaction nghiệp vụ, không chứa liên hệ/câu trả lời.',[
    uid('notification_id','Định danh thông báo.',pk=True),uid('recipient_id','Người nhận.',ref='app.users.user_id'),
    uid('post_id','Ngữ cảnh bài nếu có.',ref='app.posts.post_id',null=True),uid('claim_id','Ngữ cảnh Claim nếu có.',ref='app.claims.claim_id',null=True),
    col('event_type','varchar(24)','Loại sự kiện.',check="event_type IN ('CLAIM_RECEIVED','CLAIM_DECIDED','POST_MODERATED','ACCOUNT_BANNED')"),
    col('message_code','varchar(50)','Mã thông điệp để UI dựng nội dung, không lưu payload liên hệ.',check="message_code IN ('CLAIM_RECEIVED','CLAIM_ACCEPTED','CLAIM_REJECTED','CLAIM_CANCELLED','POST_REPORTED','POST_KEPT','POST_REMOVED','ACCOUNT_BANNED')"),
    col('read_at','timestamptz','NULL là chưa đọc.',null=True),stamp()], [
    ('notification_time','CHECK (read_at IS NULL OR read_at >= created_at)'),
    ('notification_message_event',"CHECK ((event_type = 'CLAIM_RECEIVED' AND message_code = 'CLAIM_RECEIVED') OR (event_type = 'CLAIM_DECIDED' AND message_code IN ('CLAIM_ACCEPTED','CLAIM_REJECTED','CLAIM_CANCELLED')) OR (event_type = 'POST_MODERATED' AND message_code IN ('POST_REPORTED','POST_KEPT','POST_REMOVED')) OR (event_type = 'ACCOUNT_BANNED' AND message_code = 'ACCOUNT_BANNED'))"),
    ('notification_context',"CHECK ((event_type IN ('CLAIM_RECEIVED','CLAIM_DECIDED') AND claim_id IS NOT NULL AND post_id IS NOT NULL) OR (event_type = 'POST_MODERATED' AND post_id IS NOT NULL AND claim_id IS NULL) OR (event_type = 'ACCOUNT_BANNED' AND post_id IS NULL AND claim_id IS NULL))")])
table('private.school_requests','Yêu cầu thêm trường do đại diện chưa có tài khoản gửi.',[
    uid('request_id','Mã yêu cầu trả về người gửi.',pk=True),col('university_name','varchar(200)','Tên trường đề nghị.',check="btrim(university_name) <> ''"),
    col('email_domain','varchar(253)','Tên miền xin tham gia, chuẩn hóa.',check="email_domain = lower(email_domain) AND email_domain ~ '^[a-z0-9][a-z0-9.-]*[.]edu[.]vn$'"),
    col('contact_name','varchar(150)','Người liên hệ của trường.',check="btrim(contact_name) <> ''"),
    col('contact_email','varchar(254)','Email nhận kết quả, chỉ Admin/Auth mail adapter đọc.',check="contact_email ~ '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'"),
    col('notes','text','Ghi chú tùy chọn.',null=True),col('status','varchar(10)','Vòng đời yêu cầu.',default="'PENDING'",check="status IN ('PENDING','APPROVED','REJECTED')"),
    uid('reviewer_id','Admin quyết định.',ref='app.users.user_id',null=True),uid('university_id','Trường được tạo khi APPROVED.',ref='app.universities.university_id',null=True),
    col('rejection_reason','text','Bắt buộc khi REJECTED.',null=True),col('reviewed_at','timestamptz','Thời điểm quyết định.',null=True),stamp()], [
    ('school_request_decision',"CHECK ((status = 'PENDING' AND reviewer_id IS NULL AND university_id IS NULL AND reviewed_at IS NULL AND rejection_reason IS NULL) OR (status = 'APPROVED' AND reviewer_id IS NOT NULL AND university_id IS NOT NULL AND reviewed_at IS NOT NULL AND rejection_reason IS NULL) OR (status = 'REJECTED' AND reviewer_id IS NOT NULL AND university_id IS NULL AND reviewed_at IS NOT NULL AND nullif(btrim(rejection_reason),'') IS NOT NULL))")])
table('private.school_request_campuses','Danh sách cơ sở đề nghị, tách khỏi một ô JSON/CSV để đạt 1NF.',[
    uid('request_campus_id','Định danh dòng cơ sở đề nghị.',pk=True),uid('request_id','Yêu cầu chứa cơ sở.',ref='private.school_requests.request_id'),
    col('name','varchar(150)','Tên cơ sở đề nghị.',check="btrim(name) <> ''"),col('address','text','Địa chỉ đề nghị.',check="btrim(address) <> ''")])
table('app.integration_tasks','Ghi bền vững việc cần thử lại với dịch vụ ngoài transaction CSDL.',[
    uid('task_id','Định danh tác vụ tích hợp.',pk=True),col('kind','varchar(24)','Loại thao tác.',check="kind IN ('REVOKE_SESSIONS','DELETE_OBJECT','SCHOOL_DECISION_EMAIL')"),
    uid('target_user_id','Đích thu hồi phiên.',ref='app.users.user_id',null=True),uid('request_id','Đích gửi kết quả trường.',ref='private.school_requests.request_id',null=True),
    col('object_key','text','Đích dọn object Storage.',null=True),col('status','varchar(8)','Trạng thái thử lại.',default="'PENDING'",check="status IN ('PENDING','DONE','FAILED')"),
    col('attempt_count','integer','Số lần thử.',default='0',check='attempt_count >= 0'),col('last_error_code','varchar(50)','Mã lỗi đã làm sạch, không chứa PII.',null=True),
    col('next_attempt_at','timestamptz','Thời điểm được phép thử lại.',default='CURRENT_TIMESTAMP'),stamp()], [
    ('integration_target',"CHECK ((kind = 'REVOKE_SESSIONS' AND target_user_id IS NOT NULL AND request_id IS NULL AND object_key IS NULL) OR (kind = 'SCHOOL_DECISION_EMAIL' AND request_id IS NOT NULL AND target_user_id IS NULL AND object_key IS NULL) OR (kind = 'DELETE_OBJECT' AND object_key IS NOT NULL AND btrim(object_key) <> '' AND target_user_id IS NULL AND request_id IS NULL))")])

INDEXES = [
 ('campus_name_uq','app.campuses','UNIQUE','(university_id, lower(name))','','Tên cơ sở không trùng trong cùng trường.'),
 ('category_name_uq','app.categories','UNIQUE','(lower(name))','','UC-11: chặn tên trùng cả khác hoa/thường.'),
 ('domain_university_idx','app.university_domains','','(university_id)','','Join trường và các tên miền; hỗ trợ FK.'),
 ('session_user_idx','app.sessions','','(user_id, expires_at)','','Kiểm tra/thu hồi phiên theo User; session_id đã có PK.'),
 ('post_owner_idx','app.posts','','(owner_id, created_at DESC, post_id DESC)','','UC-06: bài của tôi, phân trang ổn định.'),
 ('post_feed_idx','app.posts','','(created_at DESC, post_id DESC)',"status IN ('ACTIVE','RESOLVED')",'UC-03: bảng tin công khai mới nhất; còn join trạng thái User.'),
 ('post_campus_idx','app.posts','','(campus_id, incident_at, created_at DESC)',"status IN ('ACTIVE','RESOLVED')",'Lọc cơ sở và khoảng thời gian xảy ra sự việc.'),
 ('post_category_idx','app.posts','','(category_id, incident_at)',"status IN ('ACTIVE','RESOLVED')",'Lọc danh mục kết hợp thời gian; planner có thể BitmapAnd.'),
 ('post_type_idx','app.posts','','(post_type, created_at DESC, post_id DESC)',"status IN ('ACTIVE','RESOLVED')",'Lọc LOST/FOUND kết hợp mới nhất; không nhầm với lifecycle status.'),
 ('post_search_gin','app.posts','','USING gin (search_vector)','','Tìm từ khóa trong projection nội dung công khai, không index liên hệ/bằng chứng.'),
 ('post_queue_idx','app.posts','','(post_id)',"status = 'REPORTED'",'Tập nhỏ các bài vào hàng đợi; số báo cáo được tính khi truy vấn.'),
 ('claim_pending_uq','app.claims','UNIQUE','(post_id, claimant_id)',"status = 'PENDING'",'Một Claim đang chờ/Post/User, vẫn cho gửi lại sau REJECTED.'),
 ('claim_accepted_uq','app.claims','UNIQUE','(post_id)',"status = 'ACCEPTED'",'CSDL chặn hai Claim được chấp nhận trên cùng bài.'),
 ('claim_post_idx','app.claims','','(post_id, submitted_at DESC, claim_id)','','UC-08: danh sách Claim, bao gồm lịch sử.'),
 ('claim_user_idx','app.claims','','(claimant_id, status)','','Khóa tài khoản: tìm Claim PENDING do User gửi.'),
 ('report_pending_idx','app.reports','','(post_id)',"status = 'PENDING'",'BR-03: đếm báo cáo chưa xử lý; report_once đã bảo đảm khác người.'),
 ('report_reporter_idx','app.reports','','(reporter_id)','','Tra cứu lịch sử và hỗ trợ FK reporter.'),
 ('notification_user_idx','app.notifications','','(recipient_id, created_at DESC, notification_id DESC)','','UC-14: phân trang thông báo theo người nhận.'),
 ('notification_unread_idx','app.notifications','','(recipient_id)', 'read_at IS NULL','Đếm thông báo chưa đọc, chỉ index tập chưa đọc.'),
 ('request_pending_uq','private.school_requests','UNIQUE','(email_domain)',"status = 'PENDING'",'UC-12 E3: một yêu cầu đang chờ cho tên miền.'),
 ('request_campus_uq','private.school_request_campuses','UNIQUE','(request_id, lower(name))','','Không lặp tên cơ sở trong một yêu cầu.'),
 ('request_queue_idx','private.school_requests','','(created_at, request_id)',"status = 'PENDING'",'UC-13: lấy các yêu cầu đang chờ theo thời gian.'),
 ('audit_post_idx','app.moderation_actions','','(post_id, created_at DESC)','post_id IS NOT NULL','Lịch sử xử lý từng bài.'),
 ('audit_user_idx','app.moderation_actions','','(target_user_id, created_at DESC)','target_user_id IS NOT NULL','Lịch sử khóa tài khoản.'),
 ('task_retry_idx','app.integration_tasks','','(next_attempt_at, task_id)',"status IN ('PENDING','FAILED')",'Lấy tác vụ tích hợp đến hạn để thử lại từ API/CLI, không yêu cầu worker nền.')]

def tex(s):
    escapes={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','_':r'\_\allowbreak{}',',':r',\allowbreak{}','+':r'+\allowbreak{}','@':r'@\allowbreak{}',
             '#':r'\#','$':r'\$','{':r'\{','}':r'\}','^':r'\textasciicircum{}','~':r'\textasciitilde{}'}
    return ''.join(escapes.get(c,c) for c in str(s))

def ident(s):
    return r'\texttt{' + tex(s) + '}'

def generate():
    REPORT.mkdir(parents=True,exist_ok=True)
    sql = ['-- Generated by generate_design.py; apply once to a fresh design database.',
           '-- Supabase manages auth.users. Local tests provide only a minimal stub.',
           'CREATE SCHEMA app;', 'CREATE SCHEMA private;']
    specs=[]; relations=[]; dbml=['// Generated diagram source; auth.users is external/managed.','Table auth.users { id uuid [pk] }']
    for t in TABLES:
        defs=[]; dbcols=[]
        specs += [r'\subsubsection*{'+ident(t['name'])+'}',tex(t['description']),
            r'\begin{longtable}{|>{\raggedright\arraybackslash}p{.20\linewidth}|>{\raggedright\arraybackslash}p{.14\linewidth}|>{\raggedright\arraybackslash}p{.31\linewidth}|>{\raggedright\arraybackslash}p{.27\linewidth}|}',
            r'\hline\rowcolor{TableBlue}\tableheader{Column} & \tableheader{Type} & \tableheader{Constraints / default} & \tableheader{Description} \\ \hline\endhead']
        for c in t['columns']:
            d=c['name']+' '+c['type']; labels=[]; dbtags=[]
            if c['pk']: d+=' PRIMARY KEY'; labels+=['PK']; dbtags+=['pk']
            if not c['null']: d+=' NOT NULL'; labels+=['NN']; dbtags+=['not null']
            if c['default']:
                d+=(' '+c['default'] if c['default'].startswith('GENERATED') else ' DEFAULT '+c['default'])
                labels+=['generated STORED' if c['default'].startswith('GENERATED') else 'DEFAULT '+c['default']]
            if c['unique']: d+=' UNIQUE'; labels+=['UQ']; dbtags+=['unique']
            if c['ref']:
                target,column=c['ref'].rsplit('.',1)
                d+=f' REFERENCES {target}({column}) ON DELETE RESTRICT'
                labels+=['FK '+c['ref']+'; DELETE RESTRICT']
                card='1 : 0..1' if c['pk'] else '1 : 0..*'
                if (t['name'],c['name']) in [('private.user_contacts','user_id'),('private.post_details','post_id')]: card='1 : 1'
                if (t['name'],c['name']) == ('app.post_images','post_id'): card='1 : 1..5'
                relations.append((t['name'],c['name'],target,column,card,c['null']))
            if c['check']: d+=' CHECK ('+c['check']+')'; labels+=['CHECK '+c['check']]
            defs.append('  '+d)
            specs.append(ident(c['name'])+' & '+ident(c['type'])+' & '+tex('; '.join(labels) if labels else 'NULL được phép')+' & '+tex(c['description'])+r' \\ \hline')
            dbcols.append('  '+c['name']+' '+ ('varchar' if c['type'].startswith('varchar') else 'decimal' if c['type'].startswith('numeric') else c['type'])+(' ['+', '.join(dbtags)+']' if dbtags else ''))
        for name,body in t['constraints']: defs.append('  CONSTRAINT '+name+' '+body)
        sql.append('CREATE TABLE '+t['name']+' (\n'+',\n'.join(defs)+'\n);')
        for c in t['columns']:
            sql.append("COMMENT ON COLUMN "+t['name']+'.'+c['name']+" IS '"+c['description'].replace("'","''")+"';")
        specs.append(r'\end{longtable}')
        if t['constraints']:
            specs += [r'\textbf{Ràng buộc nhiều cột của bảng:}',r'\begin{itemize}']
            specs += [r'\item '+ident(n)+': '+tex(b)+'.' for n,b in t['constraints']]
            specs.append(r'\end{itemize}')
        dbml.append('Table '+t['name']+' {\n'+'\n'.join(dbcols)+'\n}')
    for name,tab,unique,expr,pred,why in INDEXES:
        sql.append(f'CREATE {unique+" " if unique else ""}INDEX {name} ON {tab} {expr}'+(' WHERE '+pred if pred else '')+';')
    (HERE/'schema.sql').write_text('\n\n'.join(sql)+'\n',encoding='utf-8')
    (REPORT/'05.2-table-specifications.tex').write_text('\n\n'.join(specs)+'\n',encoding='utf-8')
    for tab,colname,parent,key,card,nullable in relations:
        symbol='-' if card in ('1 : 1','1 : 0..1') else '>'
        dbml.append(f'Ref: {tab}.{colname} {symbol} {parent}.{key}')
    (HERE/'erd.dbml').write_text('\n\n'.join(dbml)+'\n',encoding='utf-8')
    (HERE/'model.json').write_text(json.dumps(dict(tables=TABLES,indexes=INDEXES,relationships=relations),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    idx=[r'\begin{longtable}{|>{\raggedright\arraybackslash}p{.23\linewidth}|>{\raggedright\arraybackslash}p{.34\linewidth}|>{\raggedright\arraybackslash}p{.35\linewidth}|}',r'\hline\rowcolor{TableBlue}\tableheader{Index} & \tableheader{Key / predicate} & \tableheader{Rationale} \\ \hline\endhead']
    for n,t,u,e,p,w in INDEXES:
        idx.append(ident(n)+' & '+ident(t)+': '+tex((u+' '+e).strip())+('; WHERE '+tex(p) if p else '')+' & '+tex(w)+r' \\ \hline')
    idx.append(r'\end{longtable}')
    (REPORT/'05.3-indexes.tex').write_text('\n'.join(idx)+'\n',encoding='utf-8')
    rel=[r'\begin{longtable}{|>{\raggedright\arraybackslash}p{.28\linewidth}|>{\raggedright\arraybackslash}p{.29\linewidth}|>{\raggedright\arraybackslash}p{.14\linewidth}|>{\raggedright\arraybackslash}p{.21\linewidth}|}',r'\hline\rowcolor{TableBlue}\tableheader{Parent key} & \tableheader{Child FK} & \tableheader{Parent:child} & \tableheader{Child to parent / delete} \\ \hline\endhead']
    for child,c,parent,key,card,nullable in relations:
        rel.append(ident(parent+'.'+key)+' & '+ident(child+'.'+c)+' & '+tex(card)+' & '+('0..1' if nullable else '1')+'; RESTRICT'+r' \\ \hline')
    rel.append(r'\end{longtable}')
    (REPORT/'05.1-relationships.tex').write_text('\n'.join(rel)+'\n',encoding='utf-8')
    print(f'Generated {len(TABLES)} tables, {sum(len(t["columns"]) for t in TABLES)} columns, {len(relations)} FKs and {len(INDEXES)} explicit indexes.')

if __name__ == '__main__': generate()
