# -*- coding: utf-8 -*-
import os
import urllib
import secrets
from datetime import datetime

from flask import (
    render_template,
    session,
    redirect,
    request,
    url_for,
    flash,
    current_app,
)

from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
)

from shop import app, db, bcrypt, storage
from .form import (
    RegistrationForm,
    LoginForm,
    CustomerRegisterForm,
    CustomerLoginForm,
)
from shop.admin.models import Admin
from shop.customers.models import Register, CustomerOrder
from shop.products.models import Addproduct, Category, Brand, Rate


# ======================================================================
#  HELPER: đồng bộ ảnh từ Firebase về static/images
# ======================================================================
def _sync_images_for_customer():
    """Tải ảnh cần thiết từ Firebase Storage về thư mục static/images nếu chưa có."""
    try:
        # kiểm tra kết nối internet
        urllib.request.urlopen("https://console.firebase.google.com/")

        must_files = ["background.png", "Assets.png", "bg.jpg", "AdminLTELogo.png"]
        for fname in must_files:
            target = os.path.join(current_app.root_path, "static/images", fname)
            if not os.path.isfile(target):
                storage.child(f"images/{fname}").download(target)

        products = Addproduct.query.all()
        for p in products:
            for img in (p.image_1, p.image_2, p.image_3):
                target = os.path.join(current_app.root_path, "static/images", img)
                if not os.path.isfile(target):
                    storage.child(f"images/{img}").download(target)

        return True
    except Exception:
        return False


def _cart_totals():
    """Tính subtotal và tổng discount giống như view carts."""
    if "Shoppingcart" not in session:
        return 0, 0

    subtotal = 0
    discount_total = 0

    for key, product in session["Shoppingcart"].items():
        price = float(product["price"])
        qty = int(product["quantity"])
        discount = int(product.get("discount", 0))

        subtotal += price * qty
        discount_total += price * qty * discount / 100

    return subtotal, discount_total


# ======================================================================
#  CÁC ROUTE HỖ TRỢ CHO ADMIN / CUSTOMER
# ======================================================================

# Đồng bộ ảnh: endpoint riêng
@app.route("/customer/synchronization", endpoint="customer_data_syn")
def customer_data_syn():
    if "email" not in session:
        flash("please login first", "danger")
        return redirect(url_for("login"))

    if _sync_images_for_customer():
        flash("Synchronization Data Success", "success")
    else:
        flash("Synchronization Data Failure, Please Reconnect Internet", "danger")

    return redirect(url_for("customer_manager"))


# Redirect thay cho /admin (tránh trùng endpoint 'admin' của module admin)
@app.route("/customer/admin_redirect", endpoint="customer_admin_redirect")
def customer_admin_redirect():
    if "email" not in session:
        flash("please login first", "danger")
        return redirect(url_for("login"))
    return redirect(url_for("admin_manager"))


# ======================================================================
#  ADMIN TẠO TÀI KHOẢN CUSTOMER
# ======================================================================
@app.route("/admin/customer_register", methods=["GET", "POST"], endpoint="customer_admin_register")
def admin_register_custormer():
    if "email" not in session:
        flash("please login first", "danger")
        return redirect(url_for("login"))

    form = CustomerRegisterForm()

    if form.validate_on_submit():
        # kiểm tra email / phone trùng trong bảng Register (customer)
        if Register.query.filter_by(email=form.email.data).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("customer_admin_register"))

        if Register.query.filter_by(phone_number=form.phone_number.data).first():
            flash("Phone number already exists!", "danger")
            return redirect(url_for("customer_admin_register"))

        gender_value = "Male" if form.gender.data == "M" else "Female"

        try:
            hash_password = bcrypt.generate_password_hash(form.password.data).decode("utf8")

            new_customer = Register(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data or "",
                last_name=form.last_name.data or "",
                phone_number=form.phone_number.data,
                gender=gender_value,
                password=hash_password,
            )

            db.session.add(new_customer)
            db.session.commit()

            flash(f"Customer '{form.username.data}' created successfully!", "success")
            return redirect(url_for("customer_admin_register"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error while creating customer: {str(e)}", "danger")
            return redirect(url_for("customer_admin_register"))

    user = Admin.query.filter_by(email=session["email"]).first()
    return render_template("admin/customer_register.html", form=form, user=user)


# ======================================================================
#  QUẢN LÝ ĐƠN HÀNG CUSTOMER (trên giao diện admin)
# ======================================================================
@app.route("/customer/orders", endpoint="customer_orders_manager")
def customer_orders_manager():
    if "email" not in session:
        flash("please login first", "danger")
        return redirect(url_for("login"))

    user = Admin.query.filter_by(email=session["email"]).all()
    customers = Register.query.all()
    orders = (
        CustomerOrder.query.filter(CustomerOrder.status != None)
        .order_by(CustomerOrder.id.desc())
        .all()
    )

    return render_template(
        "admin/manage_orders.html",
        title="Order manager page",
        user=user[0],
        orders=orders,
        customers=customers,
    )


# Nhận đơn (admin bấm Accept trong trang /admin/orders)
@app.route("/accept_order/<int:id>", methods=["GET", "POST"], endpoint="customer_accept_order")
def customer_accept_order(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer_order = CustomerOrder.query.get_or_404(id)

    # duyệt từng sản phẩm trong đơn
    for key, product in customer_order.orders.items():
        product_order = Addproduct.query.get_or_404(key)

        if product_order.stock - int(product["quantity"]) < 0:
            flash("Quantity in stock has been exhausted", "danger")
            return redirect(url_for("orders_manager"))

        product_order.stock -= int(product["quantity"])

    customer_order.status = "Accepted"
    db.session.commit()

    flash("Order accepted", "success")
    return redirect(url_for("orders_manager"))



# Hủy đơn
@app.route("/customer/delete_order/<int:id>", methods=["GET", "POST"], endpoint="customer_delete_order")
def customer_delete_order(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = CustomerOrder.query.get_or_404(id)

    if request.method == "POST":
        customer.status = "Cancelled"
        db.session.commit()
        return redirect(url_for("orders_manager"))

    return redirect(url_for("orders_manager"))


# Khóa khách
@app.route("/customer/lock_customer/<int:id>", methods=["GET", "POST"], endpoint="customer_lock_customer")
def customer_lock_customer(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = Register.query.get_or_404(id)

    if request.method == "POST":
        customer.lock = 1
        db.session.commit()
        return redirect(url_for("customer_manager"))

    return redirect(url_for("customer_manager"))


# Mở khóa khách
@app.route("/customer/unlock_customer/<int:id>", methods=["GET", "POST"], endpoint="customer_unlock_customer")
def customer_unlock_customer(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = Register.query.get_or_404(id)

    if request.method == "POST":
        customer.lock = 0
        db.session.commit()
        return redirect(url_for("customer_manager"))

    return redirect(url_for("customer_manager"))


# Xóa khách
@app.route("/customer/delete_customer/<int:id>", methods=["GET", "POST"], endpoint="customer_delete_customer")
def customer_delete_customer(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = Register.query.get_or_404(id)

    if request.method == "POST":
        rates = Rate.query.filter(Rate.register_id == id).all()
        for rate in rates:
            db.session.delete(rate)
        db.session.delete(customer)
        db.session.commit()

        flash(f"The customer {customer.username} was deleted from your database", "success")
        return redirect(url_for("customer_manager"))

    flash(f"The customer {customer.username} can't be deleted from your database", "warning")
    return redirect(url_for("customer_manager"))


# ======================================================================
#  CUSTOMER LOGIN / LOGOUT
# ======================================================================
@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = CustomerLoginForm()

    if form.validate_on_submit():
        user = Register.query.filter_by(email=form.email.data).first()

        if user is None or not bcrypt.check_password_hash(user.password, form.password.data):
            flash('Email hoặc mật khẩu không đúng', 'danger')
            return redirect(url_for('customer_login'))

        if getattr(user, 'lock', 0) == 1:
            flash('Tài khoản đã bị khóa', 'warning')
            return redirect(url_for('customer_login'))

        login_user(user)
        flash('Đăng nhập thành công', 'success')
        # có thể xử lý next ở đây nếu cần
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))

    return render_template('customers/login.html', form=form)


@app.route('/customer/logout')
@login_required
def customer_logout():
    """Đăng xuất customer."""
    logout_user()
    flash('Bạn đã đăng xuất thành công', 'success')
    return redirect(url_for('home'))


# ======================================================================
#  CUSTOMER ACCOUNT (sửa thông tin tài khoản) – tạm thời redirect về home
# ======================================================================
@app.route("/customer/update_account", methods=["GET", "POST"])
@login_required
def update_account():
    flash("Chức năng cập nhật tài khoản đang được xây dựng.", "info")
    return redirect(url_for("home"))


# ======================================================================
#  CHECKOUT – CHỈ MỘT ROUTE DUY NHẤT
# ======================================================================
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    # Không có giỏ hàng thì cho quay lại cart
    if "Shoppingcart" not in session or len(session["Shoppingcart"]) == 0:
        flash("Giỏ hàng đang trống", "warning")
        return redirect(url_for("getCart"))

    cart = session["Shoppingcart"]
    subtotal, discount_total = _cart_totals()
    grand_total = subtotal - discount_total

    # POST: tạo đơn hàng
    if request.method == "POST":
        invoice = secrets.token_hex(5)

        try:
            order = CustomerOrder(
                invoice=invoice,
                customer_id=current_user.id,
                orders=cart,              # lưu dict giỏ hàng
                status="Pending",
                date_created=datetime.utcnow(),
            )
            db.session.add(order)
            db.session.commit()

            # Xoá giỏ hàng sau khi đặt
            session.pop("Shoppingcart")
            flash("Đặt hàng thành công! Đang chờ admin duyệt.", "success")

            return render_template(
                "customers/thanks_submit.html",
                invoice=invoice,
                subtotal=subtotal,
                discount_total=discount_total,
                grand_total=grand_total,
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Có lỗi khi lưu đơn hàng: {e}", "danger")
            return redirect(url_for("getCart"))

    # GET: hiển thị trang xác nhận đơn
    return render_template(
        "customers/order.html",
        cart=cart,
        subtotals=subtotal,
        discounttotal=discount_total,
        grandtotal=grand_total,
    )
# ======================================================================