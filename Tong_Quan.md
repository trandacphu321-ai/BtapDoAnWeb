# Tổng Quan Dự Án MobileStore

Đây là ứng dụng web thương mại điện tử chuyên bán các thiết bị di động. Gần đây dự án đã được tinh chỉnh, nâng cấp giao diện chuẩn hiện đại và chuyển sang sử dụng MongoDB.

## 1. Công nghệ được sử dụng
- **Backend:** Python với framework Flask.
- **Database:** MongoDB (Đã được chuyển từ phiên bản gốc dùng bảng MySQL).
- **Frontend:** HTML, CSS thuần, JavaScript. Giao diện được thiết kế lại tối giản, hỗ trợ Dark Mode và các hiệu ứng động mượt mà.

## 2. Cấu trúc thư mục cốt lõi
- `app.py` / `run.py`: Các script khởi chạy ứng dụng web.
- `setup_mongodb.py`: Script hỗ trợ nạp dữ liệu mẫu ban đầu vào cơ sở dữ liệu MongoDB.
- `requirements.txt`: Chứa danh sách các thư viện cần thiết.
- `shop/`: Thư mục chứa module chính của website.
  - `admin/`, `carts/`, `customers/`, `products/`: Các phân hệ (Blueprint) xử lý logic của hệ thống.
  - `static/`: Chứa các tài nguyên tĩnh như CSS, font, hay JS.
  - `templates/`: Các tệp giao diện HTML.

## 3. Các phân quyền và chức năng chính
**Dành cho khách hàng (User):**
- Đăng nhập / Đăng ký tài khoản bảo mật bằng mã hóa mật khẩu.
- Xem danh sách điện thoại theo hãng / danh mục sản phẩm.
- Tìm kiếm theo tên sản phẩm.
- Thêm vào giỏ hàng, cập nhật số lượng, thanh toán giỏ hàng.

**Dành cho Ban quản trị (Admin):**
- Trang quản lý ở đường dẫn `/admin`.
- Thêm, sửa, xóa nhãn hiệu (Brand) và loại sản phẩm (Category).
- Cập nhật thông tin chi tiết điện thoại, hình ảnh đại diện, giá tiền.
