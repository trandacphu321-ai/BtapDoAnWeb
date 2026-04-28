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
    jsonify,
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
from shop.products.models import Addproduct, Category, Brand, Rate, Coupon


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

        products = Addproduct.objects().all()
        for p in products:
            for img in (getattr(p, 'image_1', None), getattr(p, 'image_2', None), getattr(p, 'image_3', None), getattr(p, 'image_4', None), getattr(p, 'image_5', None)):
                if img:
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
        if Register.objects(email=form.email.data).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("customer_admin_register"))

        if Register.objects(phone_number=form.phone_number.data).first():
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

            new_customer.save()

            flash(f"Customer '{form.username.data}' created successfully!", "success")
            return redirect(url_for("customer_admin_register"))

        except Exception as e:
            flash(f"Error while creating customer: {str(e)}", "danger")
            return redirect(url_for("customer_admin_register"))

    user = Admin.objects(email=session["email"]).first()
    return render_template("admin/customer_register.html", form=form, user=user)


# ======================================================================
#  QUẢN LÝ ĐƠN HÀNG CUSTOMER (trên giao diện admin)
# ======================================================================
@app.route("/customer/orders", endpoint="customer_orders_manager")
def customer_orders_manager():
    if "email" not in session:
        flash("please login first", "danger")
        return redirect(url_for("login"))

    user = Admin.objects(email=session["email"]).first()
    customers = Register.objects().all()
    orders = CustomerOrder.objects(status__ne=None).order_by('-id').all()

    return render_template(
        "admin/manage_orders.html",
        title="Order manager page",
        user=user,
        orders=orders,
        customers=customers,
    )





# Hủy đơn
@app.route("/customer/delete_order/<string:id>", methods=["GET", "POST"], endpoint="customer_delete_order")
def customer_delete_order(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = CustomerOrder.objects(id=id).first()

    if request.method == "POST" and customer:
        customer.status = "Cancelled"
        customer.save()
        return redirect(url_for("orders_manager"))

    return redirect(url_for("orders_manager"))


# Khóa khách
@app.route("/customer/lock_customer/<string:id>", methods=["GET", "POST"], endpoint="customer_lock_customer")
def customer_lock_customer(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = Register.objects(id=id).first()

    if request.method == "POST" and customer:
        customer.lock = True
        customer.save()
        return redirect(url_for("customer_manager"))

    return redirect(url_for("customer_manager"))


# Mở khóa khách
@app.route("/customer/unlock_customer/<string:id>", methods=["GET", "POST"], endpoint="customer_unlock_customer")
def customer_unlock_customer(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = Register.objects(id=id).first()

    if request.method == "POST" and customer:
        customer.lock = False
        customer.save()
        return redirect(url_for("customer_manager"))

    return redirect(url_for("customer_manager"))


# Xóa khách
@app.route("/customer/delete_customer/<string:id>", methods=["GET", "POST"], endpoint="customer_delete_customer")
def customer_delete_customer(id):
    if "email" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    customer = Register.objects(id=id).first()

    if request.method == "POST" and customer:
        rates = Rate.objects(user_id=id).all()
        for rate in rates:
            rate.delete()
        customer.delete()

        flash(f"The customer {customer.username} was deleted from your database", "success")
        return redirect(url_for("customer_manager"))

    flash(f"The customer can't be deleted", "warning")
    return redirect(url_for("customer_manager"))


# ======================================================================
#  CUSTOMER REGISTER
# ======================================================================
@app.route('/customer/register', methods=['GET', 'POST'], endpoint="customer_register_route")
def customer_register_route():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = CustomerRegisterForm()

    if form.validate_on_submit():
        if Register.objects(email=form.email.data).first():
            flash("Email đã tồn tại!", "danger")
            return redirect(url_for("customer_register_route"))

        if Register.objects(phone_number=form.phone_number.data).first():
            flash("Số điện thoại đã tồn tại!", "danger")
            return redirect(url_for("customer_register_route"))

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
            new_customer.save()
            
            flash("Tạo tài khoản thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("customer_login"))

        except Exception as e:
            flash(f"Lỗi: {str(e)}", "danger")
            return redirect(url_for("customer_register_route"))

    return render_template("customers/register.html", form=form)


# ======================================================================
#  CUSTOMER LOGIN / LOGOUT
# ======================================================================
#  HỆ THỐNG ĐĂNG NHẬP HỢP NHẤT (UNIFIED LOGIN)
# ======================================================================
@app.route('/login', methods=['GET', 'POST'])
def unified_login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if 'email' in session:
        return redirect(url_for('admin_manager'))

    form = CustomerLoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # 1. Kiểm tra bảng Admin
        admin = Admin.objects(email=email).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            session['email'] = email
            flash(f'Chào mừng Admin {admin.name} trở lại!', 'success')
            return redirect(url_for('admin_manager'))
            
        # 2. Kiểm tra bảng Khách hàng (Register)
        customer = Register.objects(email=email).first()
        if customer and bcrypt.check_password_hash(customer.password, password):
            if getattr(customer, 'lock', False):
                flash('Tài khoản của bạn đã bị khóa. Vui lòng liên hệ hỗ trợ.', 'danger')
                return redirect(url_for('unified_login'))
            
            login_user(customer)
            
            # Đồng bộ giỏ hàng từ DB vào session
            if getattr(customer, 'cart', None):
                session['Shoppingcart'] = customer.cart
            
            flash(f'Chào mừng {customer.username} đã quay trở lại!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
            
        flash('Email hoặc mật khẩu không chính xác.', 'danger')
    
    return render_template('customers/login.html', form=form)

# Giữ lại các route cũ nhưng redirect về /login để tránh lỗi liên kết cũ
@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    return redirect(url_for('unified_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return redirect(url_for('unified_login'))


@app.route('/logout')
def logout():
    """Đăng xuất chung cho cả Admin và Customer."""
    session.pop('email', None)
    if current_user.is_authenticated:
        # Lưu giỏ hàng vào DB trước khi thoát
        if 'Shoppingcart' in session:
            current_user.cart = session['Shoppingcart']
            current_user.save()
        logout_user()
    
    # Xóa giỏ hàng trong session (xóa trắng cho khách vãng lai/user tiếp theo)
    session.pop('Shoppingcart', None)
    
    flash('Bạn đã đăng xuất thành công', 'success')
    return redirect(url_for('home'))

# Alias cũ để không lỗi link
@app.route('/customer/logout')
def customer_logout():
    return redirect(url_for('logout'))


# ======================================================================
#  USER DASHBOARD (Bảng điều khiển người dùng)
# ======================================================================
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    # Lấy 5 đơn hàng gần đây nhất
    orders = CustomerOrder.objects(customer_id=str(current_user.id)).order_by('-date_created').limit(5)
    return render_template('customers/dashboard/overview.html', orders=orders, title="Tổng quan tài khoản")

@app.route('/customer/dashboard/orders')
@login_required
def customer_dashboard_orders():
    orders = CustomerOrder.objects(customer_id=str(current_user.id)).order_by('-date_created').all()
    return render_template('customers/dashboard/orders.html', orders=orders, title="Lịch sử mua hàng")

@app.route('/customer/dashboard/profile', methods=['GET', 'POST'])
@login_required
def customer_dashboard_profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone_number = request.form.get('phone')
        current_user.address = request.form.get('address')
        current_user.save()
        flash('Cập nhật thông tin thành công!', 'success')
        return redirect(url_for('customer_dashboard_profile'))
    return render_template('customers/dashboard/profile.html', title="Thông tin tài khoản")

@app.route('/customer/dashboard/warranty')
@login_required
def customer_dashboard_warranty():
    return render_template('customers/dashboard/warranty.html', title="Chính sách bảo hành")

@app.route('/customer/dashboard/support')
@login_required
def customer_dashboard_support():
    return render_template('customers/dashboard/support.html', title="Góp ý & Hỗ trợ")


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
                customer_id=str(current_user.id),
                orders=cart,              # lưu dict giỏ hàng
                status="Pending",
                date_created=datetime.utcnow(),
            )
            order.save()

            # --- AI Tracking: Purchase ---
            try:
                from shop.products.models import UserInteraction
                for product_id, product_details in cart.items():
                    ui = UserInteraction(
                        user_id=str(current_user.id),
                        product_id=str(product_id),
                        interaction_type='purchase',
                        weight=5
                    )
                    ui.save()
            except Exception as e:
                print("Error tracking purchase interaction:", e)
            # -----------------------------

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
#  APPLY COUPON (AJAX)
# ======================================================================
@app.route('/api/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    data = request.get_json()
    code = data.get('code', '').upper()
    
    coupon = Coupon.objects(code=code, is_active=True, expiry_date__gt=datetime.utcnow()).first()
    
    if not coupon:
        return jsonify({'success': False, 'message': 'Mã giảm giá không hợp lệ hoặc đã hết hạn.'})
    
    if coupon.used_count >= coupon.usage_limit:
        return jsonify({'success': False, 'message': 'Mã giảm giá đã hết lượt sử dụng.'})
    
    return jsonify({
        'success': True,
        'code': coupon.code,
        'discount_type': coupon.discount_type,
        'discount_value': coupon.discount_value,
        'message': 'Áp dụng mã thành công!'
    })

# ======================================================================
#  SUBMIT ORDER (Final step)
# ======================================================================
@app.route('/submit_order', methods=['POST'])
@login_required
def submit_order():
    if "Shoppingcart" not in session or len(session["Shoppingcart"]) == 0:
        flash("Giỏ hàng đang trống", "warning")
        return redirect(url_for("getCart"))

    cart = session["Shoppingcart"]
    subtotal, base_discount = _cart_totals()
    
    # Lấy thông tin từ form
    address = request.form.get('CustomerAddress')
    phone = request.form.get('CustomerPhone')
    coupon_code = request.form.get('coupon_code')
    
    # Tính toán giảm giá từ coupon
    coupon_discount = 0
    if coupon_code:
        coupon = Coupon.objects(code=coupon_code.upper(), is_active=True).first()
        if coupon and coupon.used_count < coupon.usage_limit:
            if coupon.discount_type == 'fixed':
                coupon_discount = coupon.discount_value
            else:
                coupon_discount = (subtotal * coupon.discount_value) / 100
            
            # Cập nhật lượt dùng
            coupon.used_count += 1
            coupon.save()

    grand_total = subtotal - base_discount - coupon_discount
    invoice = secrets.token_hex(5)

    try:
        order = CustomerOrder(
            invoice=invoice,
            customer_id=str(current_user.id),
            orders=cart,
            status="Pending",
            address=address,
            phone_number=phone,
            total_amount=grand_total,
            coupon_code=coupon_code.upper() if coupon_code else None,
            date_created=datetime.utcnow(),
        )
        order.save()

        # AI Tracking
        try:
            from shop.products.models import UserInteraction
            for product_id in cart.keys():
                ui = UserInteraction(user_id=str(current_user.id), product_id=str(product_id), 
                                     interaction_type='purchase', weight=5)
                ui.save()
        except: pass

        session.pop("Shoppingcart")
        flash("Đặt hàng thành công!", "success")

        return render_template(
            "customers/thanks_submit.html",
            invoice=invoice,
            subtotal=subtotal,
            discount_total=base_discount + coupon_discount,
            grand_total=grand_total,
            address=address,
            phone=phone
        )
    except Exception as e:
        flash(f"Lỗi: {e}", "danger")
        return redirect(url_for("getCart"))
# ======================================================================