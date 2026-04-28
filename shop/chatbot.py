"""
MobileStore AI Chatbot - Backend dung Gemini REST API truc tiep.
Khong phu thuoc vao google-generativeai SDK (tranh loi namespace conflict).
"""

import json
import requests as http_requests
from flask import request, jsonify
from shop import app

# =====================================================================
#  CAU HINH
# =====================================================================

GEMINI_API_KEY = "AIzaSyBl6v-Y8DeSjOvaE-0zeMO33n4NqVQyPPw"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
)

SYSTEM_PROMPT = (
    "Ban la tro ly AI ten 'MobileStore AI' cua hang ban dien thoai di dong online.\n\n"
    "QUY TAC:\n"
    "1. Luon tra loi bang tieng Viet, than thien, ngan gon (toi da 3-4 cau).\n"
    "2. Dung emoji phu hop.\n"
    "3. Chi tra loi ve mua sam, dien thoai, cua hang. Cau hoi ngoai linh vuc -> tu choi nhe nhang.\n"
    "4. Khong bia gia hoac thong tin san pham cu the. Huong dan xem truc tiep tren web.\n\n"
    "THONG TIN CUA HANG:\n"
    "- Ten: MobileStore\n"
    "- San pham: iPhone, Samsung, Xiaomi, OPPO va nhieu hang khac\n"
    "- Thanh toan: COD, chuyen khoan, MoMo, ZaloPay\n"
    "- Giao hang: HCM/HN 1-2 ngay, tinh thanh 3-5 ngay, free ship tren 2 trieu VND\n"
    "- Doi tra: mien phi 7 ngay, bao hanh 12 thang chinh hang\n"
    "- Hotline: 1900-xxxx (8h-22h) | Email: support@mobilestore.vn\n"
    "- Mua hang: nhap san pham -> chon mau + so luong -> Them vao gio -> Thanh toan"
)

# Luu lich su hoi thoai theo session (toi da 40 phan tu ~ 20 luot)
_sessions = {}


# =====================================================================
#  FALLBACK - KB cuc bo (khi API loi)
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
     'Xin chào! 👋 Mình là trợ lý AI của MobileStore. Bạn cần mình hỗ trợ gì nào?'),
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
#  GOI GEMINI REST API
# =====================================================================

def _gemini_reply(session_id, user_msg):
    """Goi Gemini API, tra string reply. None neu loi."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    history = _sessions[session_id]

    history.append({"role": "user", "parts": [{"text": user_msg}]})

    if len(history) > 40:
        history = history[-40:]
        _sessions[session_id] = history

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": history,
        "generationConfig": {
            "maxOutputTokens": 512,
            "temperature": 0.7
        }
    }

    try:
        resp = http_requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        if resp.status_code != 200:
            print(f"[Gemini] HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        reply_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        if reply_text:
            history.append({"role": "model", "parts": [{"text": reply_text}]})
            if len(_sessions) > 200:
                oldest = next(iter(_sessions))
                del _sessions[oldest]

        return reply_text or None

    except Exception as e:
        print(f"[Gemini Error] {e}")
        return None


# =====================================================================
#  API ROUTE
# =====================================================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_msg = (data.get('message') or '').strip()
    session_id = data.get('session_id') or 'default'

    if not user_msg:
        return jsonify({'reply': 'Bạn chưa nhập tin nhắn! 😅'})

    if GEMINI_API_KEY:
        reply = _gemini_reply(session_id, user_msg)
        if reply:
            return jsonify({'reply': reply})

    return jsonify({'reply': _fallback_reply(user_msg)})
