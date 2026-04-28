# Phân Tích & Kế Hoạch Nâng Cấp Website MobileStore (Phiên Bản Tích Hợp AI)

> [!IMPORTANT]
> **LƯU Ý QUAN TRỌNG NHẤT (MANDATORY RULE):** 
> Toàn bộ quá trình nâng cấp hệ thống, bao gồm cả việc tích hợp AI và chuyển đổi sang React, **TUYỆT ĐỐI KHÔNG ĐƯỢC THAY ĐỔI GIAO DIỆN NGƯỜI DÙNG (UI/UX) HIỆN TẠI**. 
> Mọi thay đổi chỉ diễn ra ở "động cơ" bên dưới (Backend, AI logic, API). Hình ảnh, màu sắc, bố cục, và trải nghiệm phía người dùng (Customer UI) phải được bảo lưu y nguyên 100%.

---

## 1. Các Vấn Đề Và Thiếu Sót Hiện Tại (Hệ thống bên dưới)

### 1.1. Về Bảo Mật & Kiến Trúc
- **Hardcode thông tin nhạy cảm:** Cần chuyển sang dùng `.env`.
- **Dữ liệu thô:** Chưa có hệ thống ngầm thu thập hành vi người dùng để phục vụ AI.
- **Caching:** Thiếu bộ nhớ đệm cho các kết quả tính toán AI nặng.

### 1.2. Về Tính Năng AI (Chưa có)
- **Thiếu tính cá nhân hóa:** Website chưa có khả năng "hiểu" người dùng để gợi ý sản phẩm phù hợp.

---

## 2. Lộ Trình Nâng Cấp Tích Hợp (Integrated Roadmap)

### Giai đoạn 1: Nền tảng & Bảo mật (Backend)
1. **Quản lý biến môi trường:** Chuyển keys vào file `.env`.
2. **Tối ưu Database:** Đánh Index và thiết kế Schema lưu trữ **Hành vi người dùng (User Interactions)** ngầm bên dưới.

### Giai đoạn 2: Thu thập dữ liệu AI & Giữ nguyên giao diện
1. **Lọc và Phân trang:** Nâng cấp logic lọc nhưng giữ nguyên style Sidebar cũ.
2. **[AI Integration] Tracking Engine:** 
   - Ghi lại các tương tác người dùng một cách âm thầm (View, Cart, Purchase).
   - Lưu vào MongoDB để làm nguyên liệu huấn luyện AI.

### Giai đoạn 3: Logic Thương mại & Gợi ý cơ bản
1. **Thanh toán trực tuyến:** Tích hợp VNPAY/MoMo vào luồng checkout hiện tại.
2. **[AI Integration] Content-based Recommendation:**
   - Triển khai thuật toán gợi ý sản phẩm tương tự.
   - Hiển thị danh sách gợi ý vào đúng các vị trí trống/thiết kế sẵn mà không làm phá vỡ layout cũ.

### Giai đoạn 4: Hệ thống Gợi ý Thông minh & Performance
1. **Tích hợp Redis:** Cache kết quả AI để tốc độ load trang vẫn nhanh như cũ.
2. **[AI Integration] Collaborative Filtering (Surprise Library):**
   - Sử dụng thuật toán **SVD** để dự đoán sở thích cá nhân hóa.
   - Hiển thị mục "Gợi ý dành riêng cho bạn" tại Trang chủ theo đúng style của các list sản phẩm hiện có.

### Giai đoạn 5: API hóa & React (Chỉ thay đổi "Động cơ")
1. **Backend Flask RESTful:** Flask chỉ đóng vai trò cung cấp dữ liệu JSON.
2. **React Customer Site:** 
   - **BẢO LƯU 100% GIAO DIỆN CŨ:** Sử dụng lại toàn bộ file CSS và cấu trúc HTML cũ. 
   - Việc dùng React chỉ để trang web chạy mượt hơn, không load lại trang, tuyệt đối không thay đổi diện mạo.

### Giai đoạn 6: Admin Manager 2.0 (Giao diện mới chỉ dành cho Admin)
- **Thiết kế lại Admin:** Đây là phần duy nhất được phép thay đổi giao diện để Admin làm việc hiệu quả hơn (Dùng Ant Design/MUI).
- **AI Dashboard:** Quản lý và theo dõi hiệu quả của hệ thống gợi ý.

---

## 3. Chi Tiết Công Nghệ AI Sử Dụng

### 3.1. Phương pháp tiếp cận (Hybrid Approach)
- **Collaborative Filtering:** Gợi ý dựa trên sự tương đồng giữa các người dùng (User-User).
- **Content-based Filtering:** Gợi ý dựa trên đặc điểm sản phẩm (Item-Item).

### 3.2. Công cụ triển khai
- **Ngôn ngữ:** Python (Flask).
- **Thư viện AI:** `scikit-surprise` (SVD, KNN), `pandas`, `numpy`.
- **Database:** MongoDB + Redis.

---
**CAM KẾT CUỐI CÙNG:** *Toàn bộ sức mạnh của AI và công nghệ mới sẽ được "giấu" khéo léo bên dưới lớp vỏ giao diện hiện tại. Người dùng sẽ chỉ cảm thấy website thông minh hơn, chạy nhanh hơn và gợi ý đúng thứ họ cần hơn, mà không hề thấy sự xa lạ hay thay đổi về mặt thẩm mỹ mà bạn đã dày công xây dựng.*
