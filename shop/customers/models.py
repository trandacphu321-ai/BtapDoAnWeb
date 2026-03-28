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
        return Register.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


# -------------------------------------------------------------------
# Kiểu dữ liệu JSON lưu trong TEXT (tương thích MySQL)
# -------------------------------------------------------------------
class JSONEncodedDict(db.TypeDecorator):
    """
    Cho phép lưu trữ dict Python vào cột TEXT trong MySQL.
    Dữ liệu sẽ được tự động json.dumps khi ghi
    và json.loads khi đọc.
    """
    impl = db.Text
    cache_ok = True  # tương thích SQLAlchemy 2.x

    def process_bind_param(self, value: Optional[Dict[str, Any]], dialect) -> str:
        if value is None:
            return "{}"
        return json.dumps(value)

    def process_result_value(self, value: Optional[str], dialect) -> Dict[str, Any]:
        if not value:
            return {}
        return json.loads(value)


# -------------------------------------------------------------------
# Bảng Register (tài khoản khách hàng) - khớp dump myshop.sql
# -------------------------------------------------------------------
class Register(db.Model, UserMixin):
    __tablename__ = "register"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    phone_number = db.Column(db.String(50), unique=True)
    gender = db.Column(db.String(5))
    password = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lock = db.Column(db.Boolean, default=False)

    def __repr__(self) -> str:
        return "<Register %r>" % self.username

    # Helper (tuỳ chọn)
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

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
class CustomerOrder(db.Model):
    __tablename__ = "customer_order"

    id = db.Column(db.Integer, primary_key=True)
    invoice = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=True)  # Pending / Accepted / Cancelled
    address = db.Column(db.String(200))
    customer_id = db.Column(db.Integer, nullable=False)
    orders = db.Column(JSONEncodedDict)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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
