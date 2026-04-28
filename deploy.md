# Kế Hoạch Triển Khai (Deployment Plan) - MobileStore V4

Dưới đây là kế hoạch chi tiết, tiêu chuẩn thực tế để đưa ứng dụng Web MobileStore (Flask + MongoDB) của bạn từ môi trường cục bộ (Local) lên Internet (Production), sẵn sàng đón khách hàng thật.

## 🏗️ 1. Tổng Quan Kiến Trúc Triển Khai (Architecture)
Để đảm bảo website hoạt động ổn định, bảo mật và chịu tải tốt, chúng ta sẽ sử dụng kiến trúc chuẩn công nghiệp cho Python Web App:
- **Ngôn ngữ / Framework:** Python (Flask).
- **WSGI Server:** Gunicorn (Thay thế cho server mặc định của Flask để xử lý nhiều requests cùng lúc).
- **Web Server / Reverse Proxy:** Nginx (Đứng ngoài cùng, nhận request HTTP/HTTPS, phục vụ các file tĩnh `static/` nhanh chóng và chuyển tiếp request động cho Gunicorn).
- **Cơ sở dữ liệu:** MongoDB Atlas (Dịch vụ Cloud Database miễn phí/trả phí của chính MongoDB, giúp không cần cài đặt và quản lý DB trên server).
- **Hosting / Máy chủ (VPS):** Ubuntu 22.04 LTS (DigitalOcean, Vultr, AWS, hoặc Vietnix/HostVN tuỳ chọn).

---

## 🛠️ 2. Các Bước Chuẩn Bị Trước Khi Triển Khai (Preparation)
1. **Đăng ký MongoDB Atlas:**
   - Tạo tài khoản trên [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
   - Tạo một Cluster (có gói Free 512MB đủ dùng cho giai đoạn đầu).
   - Lấy chuỗi kết nối (Connection String URI). Cập nhật vào mã nguồn thay cho `localhost`.
2. **Kiểm tra File `requirements.txt`:**
   - Chạy lệnh `pip freeze > requirements.txt` trên máy của bạn để lưu lại danh sách toàn bộ các thư viện cần thiết (Flask, MongoEngine, Werkzeug, v.v.).
3. **Quản lý Mã Nguồn (Version Control):**
   - Đẩy (Push) toàn bộ mã nguồn lên một kho lưu trữ riêng tư (Private Repo) trên **GitHub** hoặc **GitLab**. Không nên copy file thủ công lên server.
4. **Mua Tên Miền (Domain):**
   - Đăng ký một tên miền (VD: `mobilestore.vn`) và trỏ bản ghi `A Record` về địa chỉ IP của máy chủ VPS.

---

## 🚀 3. Các Bước Triển Khai Thực Tế Lên VPS (Execution)

### Bước 3.1: Thiết lập Máy chủ Ubuntu (VPS Setup)
1. SSH vào máy chủ VPS.
2. Cập nhật hệ thống:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. Cài đặt các công cụ cần thiết:
   ```bash
   sudo apt install python3-pip python3-venv nginx git -y
   ```

### Bước 3.2: Kéo mã nguồn & Cài đặt Môi trường
1. Clone mã nguồn từ GitHub về VPS (Ví dụ: `/var/www/mobilestore`).
2. Tạo môi trường ảo (Virtual Environment) để cô lập thư viện:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Cài đặt thư viện và Gunicorn:
   ```bash
   pip install -r requirements.txt
   pip install gunicorn
   ```

### Bước 3.3: Cấu hình Gunicorn & Systemd Service
1. Tạo một tệp dịch vụ Systemd để ứng dụng tự động chạy lại khi server khởi động lại:
   `sudo nano /etc/systemd/system/mobilestore.service`
2. Cấu hình để Gunicorn chạy file `run.py` qua một Unix Socket.
3. Kích hoạt dịch vụ:
   ```bash
   sudo systemctl start mobilestore
   sudo systemctl enable mobilestore
   ```

### Bước 3.4: Cấu hình Nginx Web Server
1. Tạo cấu hình Nginx cho tên miền:
   `sudo nano /etc/nginx/sites-available/mobilestore`
2. Thiết lập Nginx định tuyến các request đến thư mục `/static/` trực tiếp (để tăng tốc độ tải ảnh, CSS, JS), và chuyển phần còn lại sang Gunicorn Socket.
3. Liên kết và khởi động lại Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/mobilestore /etc/nginx/sites-enabled
   sudo systemctl restart nginx
   ```

### Bước 3.5: Bảo mật & SSL (HTTPS)
- Cài đặt **Certbot** để lấy chứng chỉ SSL miễn phí từ Let's Encrypt, giúp website có biểu tượng ổ khoá xanh (HTTPS) - Bắt buộc cho web bán hàng.
  ```bash
  sudo apt install python3-certbot-nginx
  sudo certbot --nginx -d mobilestore.vn
  ```

---

## 🔄 4. Giai Đoạn Hậu Triển Khai (Post-Deployment)
1. **Kiểm thử Thực tế:** Truy cập website bằng Domain/IP để kiểm tra tính năng Giỏ hàng, Đặt hàng, AI Chatbot và Thanh toán (nếu có).
2. **Ẩn Lỗi & Gỡ Lỗi:** Đảm bảo biến môi trường được đặt là `FLASK_ENV=production` và `DEBUG=False` trong file `run.py` để ẩn các thông báo lỗi nhạy cảm.
3. **Backup Dữ liệu:** Lên lịch backup Database định kỳ trên MongoDB Atlas.

---
*Ghi chú: Nếu bạn muốn một giải pháp đơn giản, "bấm là chạy" mà không cần quản lý cấu hình máy chủ lằng nhằng (Phù hợp cho đồ án/đánh giá cuối kì), chúng ta có thể chuyển hướng dùng nền tảng PaaS là **Render.com**. Việc này hoàn toàn miễn phí và chỉ mất khoảng 15-20 phút.*
