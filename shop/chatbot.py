"""
MobileStore AI Chatbot - Sử dụng cơ sở tri thức cục bộ (Local Knowledge Base).
Đã xóa hoàn toàn tích hợp Google Gemini API để tăng tính riêng tư, bảo mật và tránh phụ thuộc bên thứ ba.
"""

import json
from flask import request, jsonify
from shop import app

# =====================================================================
#  FALLBACK - KB cục bộ
# =====================================================================

FALLBACK_KB = [
    (['ban chay', 'best seller', 'pho bien', 'noi bat', 'san pham hot'],
     '🔥 Sản phẩm bán chạy: iPhone, Samsung Galaxy, Xiaomi. Xem mục "Giảm giá sốc" trên trang chủ nhé!'),
    (['doi tra', 'tra hang', 'hoan tien', 'bao hanh', 'warranty'],
     '🔄 Đổi trả miễn phí 7 ngày. Bảo hành 12 tháng chính hãng. Sản phẩm phải còn nguyên seal.'),
    (['thanh toan', 'payment', 'cod', 'chuyen khoan'],
     '💳 Thanh toán: COD, chuyển khoản ngân hàng, ví MoMo/ZaloPay. Tất cả bảo mật!'),
    (['giao hang', 'van chuyen', 'ship', 'delivery', 'bao lau'],
     '🚚 Nội thành HCM/HN: 1-2 ngày. Tỉnh khác: 3-5 ngày. Free ship đơn trên 2 triệu!'),
    (['giam gia', 'khuyen mai', 'sale', 'discount', 'voucher'],
     '🏷️ Nhiều khuyến mãi! Xem mục "Giảm giá sốc" hoặc lọc theo % giảm ở sidebar nhé.'),
    (['gia', 'bao nhieu', 'price'],
     '💰 Giá từ vài triệu đến hàng chục triệu VND. Nhấn vào sản phẩm để xem giá chi tiết!'),
    (['lien he', 'hotline', 'dia chi', 'email', 'contact'],
     '📞 Hotline: 1900-xxxx (8h-22h) | Email: support@mobilestore.vn | TP.HCM'),
    (['iphone', 'apple'], '🍎 Tìm kiếm iPhone trên thanh search để xem toàn bộ sản phẩm Apple!'),
    (['samsung', 'galaxy'], '📱 Dùng thanh tìm kiếm hoặc chọn Samsung ở sidebar để xem chi tiết!'),
    (['dat hang', 'mua hang', 'cach mua', 'them gio'],
     '🛒 Nhấn sản phẩm -> chọn màu + số lượng -> "Thêm vào giỏ" -> Thanh toán!'),
    (['dang ky', 'tao tai khoan', 'register'],
     '📝 Nhấn "Đăng ký" trên menu, điền email và mật khẩu là xong!'),
    (['dang nhap', 'login'],
     '🔐 Nhấn "Đăng nhập" trên menu, nhập email và mật khẩu đã đăng ký!'),
    (['xin chao', 'hello', 'chao ban'],
     'Xin chào! 👋 Mình là trợ lý của MobileStore. Bạn cần mình hỗ trợ gì nào?'),
    (['cam on', 'thanks', 'cam on'], 'Không có gì ạ! 😊 Rất vui được hỗ trợ bạn!'),
    (['tam biet', 'bye'], 'Tạm biệt bạn nhé! 👋 Chúc mua sắm vui vẻ! 🛒'),
]


def _fallback_reply(msg):
    lower = msg.lower()
    best_score, best_answer = 0, None
    for keys, answer in FALLBACK_KB:
        score = sum(len(k) for k in keys if k in lower)
        if score > best_score:
            best_score, best_answer = score, answer
    return best_answer or '🤔 Bạn có thể hỏi về: sản phẩm, giá cả, giao hàng, đổi trả, thanh toán nhé!'


# =====================================================================
#  API ROUTE
# =====================================================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_msg = (data.get('message') or '').strip()

    if not user_msg:
        return jsonify({'reply': 'Bạn chưa nhập tin nhắn! 😅'})

    return jsonify({'reply': _fallback_reply(user_msg)})

