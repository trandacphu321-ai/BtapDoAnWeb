# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, Optional
import json

from flask_login import UserMixin
from shop import db, login_manager


# -------------------------------------------------------------------
# Flask-Login: nạp user hiện tại dựa theo id lưu trong session (Py 3.8)
# -------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id: str) -> Optional["Register"]:
    """
    Hàm này được Flask-Login gọi để lấy user đang đăng nhập
    dựa theo ID trong session.
    """
    try:
        return Register.objects(id=user_id).first()
    except Exception:
        return None


# -------------------------------------------------------------------
# (Đã loại bỏ JSONEncodedDict do MongoEngine hỗ trợ sẵn DictField)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# Bảng Register (tài khoản khách hàng) - khớp dump myshop.sql
# -------------------------------------------------------------------
class Register(db.Document, UserMixin):
    username = db.StringField(max_length=50, unique=True)
    first_name = db.StringField(max_length=50)
    last_name = db.StringField(max_length=50)
    email = db.StringField(max_length=50, unique=True)
    phone_number = db.StringField(max_length=50, unique=True)
    gender = db.StringField(max_length=5)
    password = db.StringField(max_length=200)
    address = db.StringField(max_length=200)
    date_created = db.DateTimeField(default=datetime.utcnow)
    lock = db.BooleanField(default=False)
    cart = db.DictField()

    meta = {'collection': 'register'}

    def __repr__(self) -> str:
        return "<Register %r>" % self.username

    # Helper (tuỳ chọn)
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def get_rank(self) -> Dict[str, Any]:
        """Tính toán hạng khách hàng dựa trên tổng chi tiêu tích lũy."""
        try:
            from shop.customers.models import CustomerOrder
            # Tính tổng tiền của các đơn hàng đã hoàn thành (Accepted)
            orders = CustomerOrder.objects(customer_id=str(self.id), status='Accepted')
            total_spent = sum(order.total_amount for order in orders if order.total_amount)
            
            if total_spent < 5000000:
                return {"name": "Đồng", "color": "#cd7f32", "icon": "fa-award", "spent": total_spent, "next": 5000000}
            elif total_spent < 20000000:
                return {"name": "Bạc", "color": "#a8a29e", "icon": "fa-medal", "spent": total_spent, "next": 20000000}
            elif total_spent < 50000000:
                return {"name": "Vàng", "color": "#fbbf24", "icon": "fa-crown", "spent": total_spent, "next": 50000000}
            else:
                return {"name": "Kim Cương", "color": "#22d3ee", "icon": "fa-gem", "spent": total_spent, "next": None}
        except:
            return {"name": "Đồng", "color": "#cd7f32", "icon": "fa-award", "spent": 0, "next": 5000000}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "gender": self.gender,
            "date_created": self.date_created.isoformat() if self.date_created else None,
            "lock": bool(self.lock),
        }


# -------------------------------------------------------------------
# Bảng CustomerOrder (đơn hàng của khách) - khớp dump myshop.sql
# -------------------------------------------------------------------
class CustomerOrder(db.Document):
    invoice = db.StringField(max_length=20, unique=True, required=True)
    status = db.StringField(max_length=20)  # Pending / Accepted / Cancelled
    address = db.StringField(max_length=200)
    phone_number = db.StringField(max_length=20)
    total_amount = db.FloatField()
    coupon_code = db.StringField(max_length=50)
    customer_id = db.StringField(required=True)
    orders = db.DictField()
    date_created = db.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'customer_order'}

    def __repr__(self) -> str:
        return "<CustomerOrder %r>" % self.invoice

    # Helpers (tuỳ chọn)
    def set_orders(self, data: Dict[str, Any]) -> None:
        self.orders = data or {}

    def get_orders(self) -> Dict[str, Any]:
        return self.orders or {}

    def to_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "invoice": self.invoice,
            "status": self.status,
            "address": self.address,
            "customer_id": self.customer_id,
            "date_created": self.date_created.isoformat() if self.date_created else None,
            "items_count": len(self.get_orders()),
        }
