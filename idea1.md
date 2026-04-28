# 📱 Kế Hoạch Thiết Kế Hệ Thống Tài Khoản Người Dùng & Quy Trình Thanh Toán (Giai đoạn 7-8)

## 1. Hệ Thống Đăng Nhập Hợp Nhất (Unified Login)
Thay vì chia ra 2 đường link `/customer/login` và `/admin/login`, chúng ta sẽ sử dụng duy nhất một cổng đăng nhập tại `/login`.

### Cơ chế hoạt động:
1. **Một Form Duy Nhất:** Người dùng nhập Email/Mật khẩu vào form chung.
2. **Logic Phân Quyền (Backend):** 
   - Hệ thống quét bảng `Admin` trước. Nếu khớp -> Redirect về `/admin/ai-dashboard`.
   - Nếu không, quét bảng `Register` (Khách hàng). Nếu khớp -> Redirect về Trang cá nhân hoặc Trang chủ.
   - Nếu cả hai không khớp -> Báo lỗi.

---

## 2. Thiết Kế Trang Cá Nhân Người Dùng (User Dashboard)
Giao diện này sẽ sử dụng Sidebar bên trái để điều hướng, giữ cho phần chính diện luôn gọn gàng.

### Các phân hệ cốt lõi:
1. **Tổng quan (Overview):**
   - Lời chào cá nhân hóa: "Chào mừng trở lại, [Tên người dùng]!"
   - [x] **Tối ưu hóa Gợi ý (AI Suggestions):** Chỉ hiển thị phần "Gợi ý dành riêng cho bạn" tại trang chủ cho người dùng đã đăng nhập (ẩn đối với khách vãng lai).
   - [x] **Đồng bộ Giỏ hàng thông minh:** Tự động lưu giỏ hàng vào Database khi đăng xuất và nạp lại khi đăng nhập. Giỏ hàng sẽ được xóa trắng trong session sau khi logout để bảo mật thông tin.
   - Card tóm tắt: Tổng đơn hàng, Số sản phẩm trong giỏ.
   - Bảng **Đơn hàng gần đây**: Hiển thị 3 đơn hàng mới nhất với trạng thái (Đang chờ, Đã giao).

2. **Lịch sử mua hàng (Order History):**
   - Danh sách chi tiết toàn bộ các đơn hàng từ trước đến nay.
   - Cho phép xem chi tiết từng đơn (Mua những gì, bao nhiêu tiền, ngày nào).

3. **Thông tin tài khoản (Account Info):**
   - Cho phép cập nhật Họ tên, SĐT, Địa chỉ mặc định.
   - Thay đổi mật khẩu an toàn.

4. **Chính sách bảo hành (Warranty Policy):**
   - Hiển thị các quy định bảo hành 1 đổi 1 trong 30 ngày, bảo hành 12 tháng của Apple/Samsung...
   - Thiết kế dạng Accordion (bấm vào để mở rộng nội dung) để tránh rối mắt.

5. **Góp ý - Hỗ trợ - Bảo hành (Support Center):**
   - **Form gửi yêu cầu:** Khách hàng có thể gửi tin nhắn phản hồi hoặc yêu cầu bảo hành cho một đơn hàng cụ thể.
   - Các tin nhắn này sẽ được đẩy thẳng về Admin Dashboard.

6. **Đăng xuất:** Nút đỏ nổi bật ở cuối Sidebar.

---

## 3. Cải Thiện Quy Trình Thanh Toán (Smart Checkout)
Quy trình sẽ được chia thành các bước rõ ràng (Stepper) để người dùng không bị choáng ngợp.

### Luồng xử lý mới:
1. **Xác nhận giỏ hàng:** Người dùng kiểm tra lại các món đồ.
2. **Nhập thông tin giao hàng (Form Popup/Section):**
   - Tự động điền (Auto-fill) thông tin nếu người dùng đã lưu địa chỉ trong trang Cá nhân.
   - Yêu cầu: Họ tên, SĐT nhận hàng, Địa chỉ chi tiết, Ghi chú.
3. **Thanh toán & Thông báo:**
   - Sau khi ấn "Xác nhận thanh toán", hệ thống hiển thị **Animation Thành Công** (Dấu tích xanh xoay tròn) cực kỳ chuyên nghiệp.
   - Hiển thị nút: "Về trang chủ" và "Xem đơn hàng của tôi".

---

## 4. Hệ Thống Thông Báo Admin (Real-time Notification)
Để Admin không bỏ lỡ đơn hàng:
- **Thông báo nháy đỏ:** Tại Sidebar của Admin, mục "Đơn đặt hàng" sẽ hiện số lượng đơn mới (ví dụ: `Đơn hàng [5]`).
- **Web Push Notification:** Hiển thị thông báo nhỏ ở góc màn hình Admin mỗi khi có đơn hàng mới hoặc có góp ý mới từ khách hàng.

---

## 5. Cải Thiện Thêm Từ Antigravity (Idea bổ sung)
- **Hệ thống Rank khách hàng:** Dựa trên lịch sử mua hàng, hiển thị hạng (Đồng, Bạc, Vàng, Kim Cương) tại trang Cá nhân để khuyến khích khách quay lại mua tiếp.
- **Theo dõi đơn hàng (Tracking):** Hiển thị thanh tiến trình đơn hàng (Đã xác nhận -> Đang đóng gói -> Đang giao -> Hoàn thành) để khách hàng yên tâm.

---

## 6. Sửa Lỗi Logic Giỏ Hàng (Cart Price Fix)
Hiện tại hệ thống đang gặp lỗi: Giá hiển thị của phiên bản (ví dụ 512GB) không đồng bộ với tổng tiền thanh toán (vẫn tính theo giá cơ bản).

### Giải pháp khắc phục:
1. **Đồng bộ Variant Price:** Viết lại hàm JavaScript để khi người dùng đổi "Phiên bản" trong giỏ hàng, giá đơn lẻ và tổng tiền (Price Details) phải nhảy theo ngay lập tức.
2. **Backend Validation:** Khi nhấn "Thanh toán", Backend phải kiểm tra lại một lần nữa giá của phiên bản đó trong Database để đảm bảo số tiền cuối cùng là chính xác tuyệt đối, tránh việc người dùng can thiệp vào giá ở phía trình duyệt.

---

## 7. Hệ Thống Mã Giảm Giá (Discount Coupons)
Tạo động lực mua hàng bằng các chương trình khuyến mãi.

### Phía Admin (Quản lý):
- Giao diện tạo mã mới: Nhập mã (ví dụ: `MOBILESTORE2024`), % giảm giá hoặc số tiền giảm cố định, ngày hết hạn, và số lượt sử dụng tối đa.
- Danh sách quản lý mã: Xem mã nào đang hiệu lực, mã nào đã hết hạn.

### Phía Người dùng (Checkout):
- Ô nhập mã tại trang Thanh toán.
- Kiểm tra mã ngầm (AJAX): Nếu mã hợp lệ, trừ tiền trực tiếp vào tổng bill và hiển thị thông báo "Áp dụng mã thành công".

---

## 8. Quy Trình Vận Chuyển & Tra Cứu Đơn Hàng (Order Workflow & Tracking)
Tối ưu hóa sự minh bạch trong quá trình từ khi đặt hàng đến khi nhận hàng.

### Luồng Trạng Thái Thông Minh:
1.  **Xác nhận đơn hàng (Admin):** 
    - Khi Admin nhấn "Chấp nhận" trong mục quản lý đơn hàng chờ duyệt, trạng thái đơn hàng sẽ tự động chuyển sang **"Đang giao" (Shipping)**. 
    - Phía người dùng sẽ thấy thanh tiến trình nhảy sang bước vận chuyển.
2.  **Quản lý Giao hàng (Admin):**
    - Bổ sung danh mục **"Đơn giao hàng"** riêng biệt trong Sidebar Admin. 
    - Danh mục này chỉ chứa các đơn đang trên đường giao. Admin cần xác nhận "Giao thành công" tại đây để kết thúc quy trình.
3.  **Xác nhận Hoàn thành:**
    - Chỉ sau khi Admin xác nhận giao thành công, trạng thái phía khách hàng mới hiển thị là **"Giao hàng thành công"**.

### Tính năng Tra cứu Đơn hàng Nhanh (Quick Tracking):
- **Vị trí:** Tích hợp một thanh tra cứu nhỏ hoặc Icon "Tra cứu đơn hàng" tại Header của Website.
- **Cơ chế:** Khách hàng (ngay cả khách vãng lai) chỉ cần nhập **Mã đơn hàng (Invoice ID)** vào là có thể xem nhanh trạng thái hiện tại (Đang chờ/Đang giao/Đã giao) mà không nhất thiết phải đăng nhập vào Dashboard.

---

## 9. Quản lý Doanh thu & Xuất báo cáo (Revenue Management)
Tối ưu hóa việc theo dõi tình hình kinh doanh cho chủ cửa hàng.

### Chức năng chính:
1. **Menu Doanh thu riêng biệt:** 
   - Thêm một mục "Thống kê Doanh thu" nằm ngay trên Sidebar Admin.
   - Giao diện hiển thị tổng doanh thu theo Ngày, Tháng, Năm.
   - Biểu đồ tăng trưởng doanh thu trực quan.
2. **Xuất báo cáo Excel:**
   - Tích hợp nút **"Xuất Excel"** cho phép tải xuống danh sách đơn hàng đã hoàn thành kèm chi tiết doanh thu.
   - Định dạng file chuyên nghiệp: Mã đơn, Khách hàng, Ngày đặt, Tổng tiền, Trạng thái.

---

## ✅ Checklist Tiến Độ (Update: 2026-04-22)

### 🏁 Đã hoàn thành (Done):
- [x] **Sửa lỗi Logic Giỏ hàng:** Giá phiên bản (Capacity) đã đồng bộ chính xác với Backend và Frontend.
- [x] **Hệ thống Mã giảm giá (Coupons):** 
  - [x] Admin có thể tạo/xóa mã giảm giá.
  - [x] Khách hàng có thể áp dụng mã trực tiếp tại trang thanh toán (AJAX).
- [x] **Cải thiện Checkout:** 
  - [x] Form nhập thông tin giao hàng chuyên nghiệp.
  - [x] Trang thông báo đặt hàng thành công "Thanks Submit" cao cấp.
- [x] **Hệ thống Đăng nhập hợp nhất (Unified Login):** Đã hợp nhất `/login` cho cả Admin và Customer.
- [x] **User Dashboard (Trang cá nhân):** Đầy đủ các phân hệ Tổng quan, Đơn hàng, Hồ sơ, Bảo hành, Hỗ trợ.
- [x] **Database:** Cập nhật Model `CustomerOrder` và `Coupon` trong MongoDB.
- [x] **Cập nhật 22/04/2026 (Modern UI & Detail Page):**
  - [x] **Refactor Trang Chi tiết sản phẩm:** Giao diện thẻ (card) hiện đại, viền đậm 2px, đổ bóng premium.
  - [x] **Tính năng chọn biến thể:** Bổ sung chọn Màu sắc và Dung lượng với logic tính giá tự động.
  - [x] **Trải nghiệm mua hàng:** Tích hợp AJAX thêm vào giỏ hàng với thông báo Toast và nút Mua ngay.
  - [x] **Fix Layout Footer:** Sửa lỗi Footer bị co hẹp, đảm bảo luôn hiển thị 100% chiều rộng.
  - [x] **Tối ưu Dashboard:** Triển khai chế độ "Zoom" (chữ to, khoảng cách rộng) giúp dễ nhìn và chuyên nghiệp hơn.
  - [x] **Sửa lỗi hệ thống:** Fix lỗi BuildError form đánh giá và các cảnh báo cú pháp CSS/Jinja.
- [x] **Cập nhật 24/04/2026 (UI/UX Evolution):**
  - [x] **Nâng cấp Breadcrumb:** Tái thiết kế thanh điều hướng theo phong cách Minimalist Premium, sử dụng icon Chevron và typography hiện đại.
  - [x] **Sửa lỗi Layout Overlap:** Xử lý triệt để việc Menu đè lên nội dung bằng cách tối ưu lại hệ thống định vị (Positioning) trong CSS toàn cục.
  - [x] **Auto-playing Gallery:** Triển khai tính năng tự động chuyển ảnh sản phẩm (3s/lần) với hiệu ứng Fade/Scale mượt mà và logic tạm dừng thông minh khi người dùng tương tác.
  - [x] **Dropdown Menu thông minh:** Hoàn thiện tính năng hiển thị thương hiệu (Brands) theo danh mục khi di chuột vào thanh điều hướng chính.
  - [x] **Dọn dẹp hệ thống script:** Khắc phục xung đột jQuery, giúp website vận hành ổn định và không còn lỗi console.

### 🚀 Tính năng nâng cao (Sắp tới):
- [x] **Quy trình Giao hàng 2 lớp:**
  - [x] Phân hệ "Đơn giao hàng" cho Admin.
  - [x] Logic chuyển trạng thái tự động sang "Đang giao".
- [x] **Công cụ Tra cứu đơn hàng nhanh:** Ô tìm kiếm Mã hóa đơn tại Header.
- [x] **Thông báo Admin:** Hệ thống thông báo thời gian thực khi có đơn hàng mới.
- [x] **Hệ thống Rank khách hàng:** Tính điểm tích lũy và xếp hạng.
- [ ] **Quản lý Doanh thu:** Tạo menu và giao diện thống kê doanh thu Admin.
- [ ] **Xuất dữ liệu Excel:** Tính năng download báo cáo doanh thu định dạng .xlsx.

---

## 🚀 10. Ý tưởng Nâng cấp Đột phá (Future Vision - Consultation)

Dưới đây là các đề xuất từ Antigravity nhằm biến MobileStore thành một nền tảng e-commerce chuyên nghiệp và có chiều sâu hơn:

### A. Trải nghiệm mua sắm thông minh (AI & Logic):
1.  **So sánh sản phẩm (Smart Comparison):** 
    - Cho phép chọn 2-3 điện thoại để so sánh thông số kỹ thuật (Chip, RAM, Camera, Pin) trên một bảng đối chiếu trực quan.
2.  **Bộ lọc tìm kiếm nâng cao (Dynamic Filters):** 
    - Tích hợp bộ lọc AJAX tại trang danh mục: Lọc theo khoảng giá, thương hiệu, và thông số máy mà không cần load lại trang.
3.  **Thông báo khi có hàng (Restock Notification):** 
    - Khi một phiên bản hết hàng, người dùng có thể để lại Email/SĐT để hệ thống tự động thông báo khi có hàng về.

### B. Tăng cường tương tác và giữ chân khách hàng:
4.  **Hệ thống Wishlist (Sản phẩm yêu thích):** 
    - Thêm icon trái tim tại mỗi sản phẩm để người dùng lưu lại danh sách các món đồ muốn mua sau này.
5.  **Tích điểm đổi quà (Mobile Points):** 
    - Mỗi đơn hàng thành công sẽ tích lũy điểm thưởng. Điểm này có thể dùng để trừ tiền trực tiếp hoặc đổi lấy mã giảm giá.
6.  **Chế độ Dark Mode hoàn chỉnh:** 
    - Tích hợp trình chuyển đổi giao diện Sáng/Tối giúp bảo vệ mắt và tạo vẻ ngoài công nghệ hơn cho website.

### C. UI/UX & Chuyên nghiệp hóa:
7.  **Video Review Popup:** 
    - Nút "Xem nhanh Review" mở ra một cửa sổ nổi (Modal) trình chiếu video đánh giá từ YouTube, giúp khách hàng quyết định mua nhanh hơn.
8.  **Flash Sale Countdown:** 
    - Đồng hồ đếm ngược cho các sản phẩm đang có chương trình giảm giá giới hạn thời gian ngay tại trang chủ.
9.  **Hệ thống đánh giá có hình ảnh:** 
    - Nâng cấp phần Review cho phép khách hàng upload ảnh thực tế sản phẩm để tăng độ uy tín cho gian hàng.

### D. Tối ưu hóa vận hành (Admin):
    - Hệ thống cảnh báo tự động trong Admin Dashboard khi một mã hàng sắp hết (ví dụ còn dưới 5 sản phẩm).

---

## 🤖 11. Hệ thống Gợi ý Sản phẩm Thông minh (Smart Recommendation System)

Đây là các phương án nâng cấp sâu cho hệ thống gợi ý nhằm tối ưu hóa tỷ lệ chuyển đổi (CR) và giá trị đơn hàng trung bình (AOV):

### A. Gợi ý dựa trên Hành vi (Behavioral Based):
1.  **Gợi ý cá nhân hóa (Personalized for You):** 
    - Hiển thị sản phẩm dựa trên lịch sử xem hàng và các sản phẩm đã click của chính người dùng đó.
2.  **Sản phẩm vừa xem (Recently Viewed):** 
    - Một thanh trượt (slider) nhỏ ở cuối mỗi trang để khách hàng dễ dàng quay lại các sản phẩm họ vừa quan tâm.
3.  **Mua cùng nhau (Frequently Bought Together):** 
    - Tại trang chi tiết sản phẩm, gợi ý các phụ kiện đi kèm thường được mua cùng (Ví dụ: iPhone -> Gợi ý thêm Ốp lưng, Sạc 20W, AirPods).

### B. Chiến lược tăng giá trị đơn hàng (Upselling & Cross-selling):
4.  **Nâng cấp đời máy (You might also like):** 
    - Nếu người dùng đang xem iPhone 15, hãy gợi ý iPhone 16 hoặc bản Pro Max với thông điệp: "Chỉ thêm X triệu để sở hữu công nghệ mới nhất".
5.  **Gói Combo tiết kiệm (Bundle Deals):** 
    - Tự động gợi ý các gói sản phẩm (ví dụ: Combo Học tập: Laptop + Chuột + Balo) với giá ưu đãi hơn khi mua lẻ.

### C. Gợi ý theo Xu hướng & Cộng đồng (Social Proof):
6.  **Sản phẩm đang Hot (Trending Now):** 
    - Hiển thị các sản phẩm có lượt click hoặc số lượng bán tăng đột biến trong 24h qua.
7.  **Khách hàng cũng đã mua (Customers also bought):** 
    - Gợi ý sản phẩm dựa trên dữ liệu mua sắm của các khách hàng khác có sở thích tương đồng.

### D. Cơ chế hiển thị thông minh:
8.  **Gợi ý tại Giỏ hàng (Cart Cross-sell):** 
    - Trước khi thanh toán, hiển thị các sản phẩm nhỏ (Dán cường lực, cáp sạc) để khách hàng tiện tay "nhặt thêm".
9.  **Gợi ý qua Email (Abandoned Cart Recovery):** 
    - Tự động gửi mail nhắc nhở kèm gợi ý các sản phẩm tương tự nếu khách hàng bỏ quên giỏ hàng quá 24h.

---

## 🎨 12. Tái cấu trúc Giao diện Điều hướng (Vertical Navigation & Top Rated)

Để tối ưu hóa không gian hiển thị và mang lại trải nghiệm giống các sàn thương mại điện tử lớn (như Shopee, Tiki, hoặc Amazon), chúng ta sẽ thực hiện tái cấu trúc lại thanh Menu:

### A. Chuyển đổi sang Menu Dọc (Vertical Navigation Bar):
1.  **Chuyển từ Ngang sang Dọc:**
    - Thay vì nằm dàn ngang ở dưới thanh tìm kiếm, toàn bộ danh mục sản phẩm (Điện thoại, Laptop, Đồng hồ...) sẽ được gom lại thành một thanh Menu dọc (Sidebar) đặt cố định ở bên trái màn hình.
    - Việc này giúp người dùng dễ dàng lướt qua tất cả danh mục mà không bị rối mắt, đặc biệt hữu ích khi số lượng danh mục tăng lên.
2.  **Hiệu ứng Hover & Dropdown:**
    - Khi di chuột (hover) vào từng danh mục chính ở thanh dọc, các hãng (Brands) tương ứng sẽ trượt ra (fly-out) mượt mà sang bên phải.

### B. Tận dụng Không gian hiển thị (Top Rated Products):
3.  **Khu vực "Sản phẩm yêu thích nhất":**
    - Do Menu dọc đã dời sang trái, không gian trống bên phải sẽ được tận dụng tối đa để tạo một khối Banner/Slider động.
    - Thay vì hiển thị quảng cáo tĩnh, khu vực này sẽ hiển thị danh sách **"Sản phẩm yêu thích nhất"** (Top Rated / Best Reviews) được hệ thống tự động lọc ra dựa trên điểm đánh giá trung bình (ví dụ: các sản phẩm đạt 4.8 - 5.0 sao) và số lượng đánh giá cao từ khách hàng.
4.  **Lợi ích kép (Dual Benefit):**
    - Vừa lấp đầy không gian trống một cách thẩm mỹ.
    - Vừa sử dụng *Social Proof* (Bằng chứng xã hội) ngay lập tức khi khách hàng vừa vào trang chủ để tăng độ tin cậy và kích thích quyết định mua sắm ngay từ ánh nhìn đầu tiên.
