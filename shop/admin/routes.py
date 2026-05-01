import os
import urllib
from itertools import product
import pandas as pd
import io
from flask import send_file

# Bổ sung user
# from .form import LoginForm
# from shop.customers.models import Register
# from flask_login import login_user
# Kết thúc bổ sung user



from flask import render_template, session, redirect, request, url_for, flash, session, current_app
from shop import app, db, bcrypt
from .form import RegistrationForm, LoginForm, CustomerRegisterForm
from .models import Admin
from shop.customers.models import Register, CustomerOrder
from shop.products.models import Addproduct, Brand, Category, Rate, Coupon
from datetime import datetime


def synchronization():
    try:
        # Mocking Firebase behavior logic bypassing since project requires payment config
        return True
    except Exception as e:
        print(e)
        return False

@app.route('/synchronization')
def data_syn():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    if synchronization():
        flash(f'Synchronization Data Success', 'success')
        return redirect(url_for('admin_manager'))
    else:
        flash(f'Synchronization Data Failure, Please Reconnect Internet', 'danger')
        return redirect(url_for('admin_manager'))

@app.route('/admin/customer_register', methods=['GET', 'POST'])
def admin_register_custormer():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    form = CustomerRegisterForm()
    if form.validate_on_submit():
        if Admin.objects(email=form.email.data).first():
            flash(f'Email Used!', 'danger')
            return redirect(url_for('admin_register_custormer'))
        if Register.objects(email=form.email.data).first():
            flash(f'Email Used!', 'danger')
            return redirect(url_for('admin_register_custormer'))
        if Register.objects(phone_number=form.phone_number.data).first():
            flash(f'Phone Number Used!', 'danger')
            return redirect(url_for('admin_register_custormer'))
        try:
            hash_password = bcrypt.generate_password_hash(form.password.data).decode('utf8')
            register = Register(username=form.username.data, email=form.email.data, first_name=form.first_name.data,
                                last_name=form.last_name.data, phone_number=form.phone_number.data,
                                gender=form.gender.data,
                                password=hash_password)
            register.save()
            flash(f'Register account " {form.first_name.data} {form.last_name.data} " success', 'success')
            return redirect(url_for('admin_register_custormer'))
        except:
            flash(f'Error!', 'danger')
            return redirect(url_for('admin_register_custormer'))
    user = Admin.objects(email=session['email']).first()
    return render_template('admin/customer_register.html', form=form, user=user)


@app.route('/admin')
def admin():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    return redirect(url_for('admin_manager'))
# @app.route("/customer/admin_redirect", endpoint="customer_admin_redirect")
# def customer_admin_redirect():
#     """Redirect tránh trùng với admin route chính"""
#     if "email" not in session:
#         flash("please login first", "danger")
#         return redirect(url_for("login"))
#     return redirect(url_for("admin_manager"))


@app.route('/admin_manager')
def admin_manager():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    admins = Admin.objects().all()
    return render_template('admin/admin-manager.html', title='Admin manager page', user=user, admins=admins)


@app.route('/customer_manager')
def customer_manager():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    customers = Register.objects().all()
    return render_template('admin/customer_manager.html', title='Customer manager page', user=user,
                           customers=customers)


@app.route('/admin/orders')
def orders_manager():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    customers = Register.objects().all()

    orders = CustomerOrder.objects(status__ne=None).order_by('-id').all()
    return render_template('admin/manage_orders.html', title='Order manager page', user=user, orders=orders,
                           customers=customers)


@app.route('/accept_order/<string:id>', methods=['GET', 'POST'])
def accept_order(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    
    customer_order = CustomerOrder.objects(id=id).first()
    if not customer_order: 
        return redirect(url_for('orders_manager'))
    
    # Duyệt trừ kho
    for key, product in customer_order.orders.items():
        product_order = Addproduct.objects(id=key).first()
        if product_order:
            if (product_order.stock - int(product['quantity'])) >= 0:
                product_order.stock -= int(product['quantity'])
                product_order.save()
            else:
                flash(f'Sản phẩm {product_order.name} đã hết hàng!', 'danger')
                return redirect(url_for('orders_manager'))
    
    # Chuyển sang trạng thái Đang giao
    customer_order.status = 'Shipping'
    customer_order.save()
    flash(f'Đã chấp nhận đơn hàng #{customer_order.invoice}. Trạng thái: Đang giao.', 'success')
    return redirect(url_for('orders_manager'))

@app.route('/complete_order/<string:id>', methods=['POST'])
def complete_order(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    
    customer_order = CustomerOrder.objects(id=id).first()
    if customer_order:
        customer_order.status = 'Accepted'
        customer_order.save()
        flash(f'Đã xác nhận giao hàng thành công đơn #{customer_order.invoice}!', 'success')
    return redirect(url_for('orders_manager'))

@app.route('/track_order', methods=['GET', 'POST'])
def track_order():
    # Ưu tiên lấy từ request.args (nếu dùng link tra cứu trực tiếp) hoặc request.form
    invoice = request.args.get('invoice_id') or request.form.get('invoice_id')
    order = None
    
    if invoice:
        # Sử dụng __iexact để tra cứu không phân biệt hoa thường
        order = CustomerOrder.objects(invoice__iexact=invoice.strip()).first()
        if not order:
            # Chỉ flash nếu người dùng vừa thực hiện nhấn nút kiểm tra
            flash(f'Không tìm thấy thông tin cho hóa đơn #{invoice}', 'warning')
            
    return render_template('customers/track_order.html', order=order, invoice=invoice, title="Tra cứu đơn hàng")


@app.route('/delete_order/<string:id>', methods=['GET', 'POST'])
def delete_order(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    customer = CustomerOrder.objects(id=id).first()
    if request.method == "POST" and customer:
        customer.status = "Cancelled"
        customer.save()
        return redirect(url_for('orders_manager'))
    return redirect(url_for('orders_manager'))


@app.route('/lock_customer/<string:id>', methods=['GET', 'POST'])
def lock_customer(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    customer = Register.objects(id=id).first()
    if request.method == "POST" and customer:
        customer.lock = True
        customer.save()
        return redirect(url_for('customer_manager'))
    return redirect(url_for('customer_manager'))


@app.route('/unlock_customer/<string:id>', methods=['GET', 'POST'])
def unlock_customer(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    customer = Register.objects(id=id).first()
    if request.method == "POST" and customer:
        customer.lock = False
        customer.save()
        return redirect(url_for('customer_manager'))
    return redirect(url_for('customer_manager'))


@app.route('/delete_customer/<string:id>', methods=['GET', 'POST'])
def delete_customer(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    customer = Register.objects(id=id).first()
    if request.method == "POST" and customer:
        rates = Rate.objects(user_id=id).all()
        for rate in rates:
            rate.delete()
        customer.delete()
        flash(f"The customer {customer.username} was deleted from your database", "success")
        return redirect(url_for('customer_manager'))
    flash(f"The customer can't be deleted", "warning")
    return redirect(url_for('customer_manager'))


@app.route('/delete_admin/<string:id>', methods=['GET', 'POST'])
def delete_admin(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    admin = Admin.objects(id=id).first()
    if request.method == "POST" and admin:
        admin.delete()
        flash(f"The admin {admin.name} was deleted from your database", "success")
        return redirect(url_for('admin_manager'))
    flash(f"The admin can't be deleted", "warning")
    return redirect(url_for('admin_manager'))


@app.route('/product')
def product():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    products = Addproduct.objects().all()
    user = Admin.objects(email=session['email']).first()
    return render_template('admin/index.html', title='Product page', products=products, user=user)

@app.route('/brands')
def brands():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    brands = Brand.objects().order_by('-id').all()
    user = Admin.objects(email=session['email']).first()
    # Mock category join logic since Mongo uses referenced object directly in templates
    return render_template('admin/manage_brand.html', title='brands', brands=brands, user=user)

@app.route('/categories')
def categories():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    categories = Category.objects().order_by('-id').all()
    user = Admin.objects(email=session['email']).first()
    return render_template('admin/manage_brand.html', title='categories', categories=categories, user=user)


@app.route('/admin/changepassword', methods=['GET', 'POST'])
def changes_password():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    old_password = request.form.get('oldpassword')
    new_password = request.form.get('newpassword')
    if request.method == "POST":
        if not bcrypt.check_password_hash(user.password, old_password.encode('utf8')):
            flash(f'Old passwords do not match!', 'danger')
            return redirect(url_for('changes_password'))
        user.password = bcrypt.generate_password_hash(new_password).decode('utf8')
        flash(f'Change Password Complete!', 'success')
        user.save()
        return redirect(url_for('changes_password'))
    return render_template('admin/change_password.html', title='Change Password', user=user)

@app.route('/admin/register', methods=['GET', 'POST'])
def register():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        hash_password = bcrypt.generate_password_hash(form.password.data).decode('utf8')
        user = Admin(name=form.name.data, username=form.username.data, email=form.email.data, password=hash_password)
        user.save()
        flash(f' Wellcom {form.name.data} Thanks for registering', 'success')
        return redirect(url_for('register'))
    user = Admin.objects(email=session['email']).first()
    return render_template('admin/admin_register.html', form=form, title='Registration page', user=user)


@app.route('/admin/login_old', methods=['GET', 'POST'])
def login_old():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = Admin.objects(email=form.email.data).first()
        password = form.password.data.encode('utf8')
        if user and bcrypt.check_password_hash(user.password, password):
            session['email'] = form.email.data
            flash(f'welcome {form.email.data} you are logedin now', 'success')
            return redirect(url_for('admin'))
        else:
            flash(f'Wrong email and password', 'danger')
            return redirect(url_for('login_old'))
    return render_template('admin/login.html', title='Login page', form=form)


@app.route('/admin/logout_old')
def logout_old():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
    else:
        session.pop('email', None)
    return redirect(url_for('unified_login'))


# ======================================================================
#  GIAI ĐOẠN 6: AI Dashboard
# ======================================================================
@app.route('/admin/ai-dashboard')
def ai_dashboard():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    return render_template('admin/ai_dashboard.html', title='AI Dashboard', user=user)

# ======================================================================
#  Hệ Thống Mã Giảm Giá (Coupons)
# ======================================================================
@app.route('/admin/coupons')
def manage_coupons():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    coupons = Coupon.objects().all()
    return render_template('admin/manage_coupons.html', title='Quản lý Mã giảm giá', user=user, coupons=coupons)

@app.route('/admin/revenue')
def revenue_report():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    user = Admin.objects(email=session['email']).first()
    
    # Lấy tất cả đơn hàng đã hoàn thành
    completed_orders = CustomerOrder.objects(status='Accepted').order_by('-date_created')
    
    # Tính toán doanh thu
    total_revenue = sum(o.total_amount for o in completed_orders if o.total_amount)
    
    # Thống kê theo tháng (đơn giản)
    monthly_stats = {}
    for o in completed_orders:
        month_key = o.date_created.strftime('%Y-%m')
        monthly_stats[month_key] = monthly_stats.get(month_key, 0) + (o.total_amount or 0)
    
    # Sắp xếp tháng
    sorted_months = sorted(monthly_stats.items(), reverse=True)
    
    return render_template('admin/revenue.html', 
                           title='Thống kê Doanh thu', 
                           user=user, 
                           orders=completed_orders,
                           total_revenue=total_revenue,
                           monthly_stats=sorted_months)

@app.route('/admin/export-revenue')
def export_revenue():
    if 'email' not in session:
        flash(f'please login first', 'danger')
        return redirect(url_for('unified_login'))
    
    completed_orders = CustomerOrder.objects(status='Accepted').order_by('-date_created')
    
    data = []
    for o in completed_orders:
        data.append({
            'Mã đơn hàng': f"#{o.invoice}",
            'Ngày đặt': o.date_created.strftime('%d/%m/%Y %H:%M'),
            'Khách hàng ID': o.customer_id,
            'Số điện thoại': o.phone_number,
            'Địa chỉ': o.address,
            'Tổng tiền (VND)': o.total_amount,
            'Trạng thái': 'Hoàn thành'
        })
    
    df = pd.DataFrame(data)
    
    # Xuất ra buffer
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Doanh Thu')
        output.seek(0)
    except Exception as e:
        flash(f'Lỗi khi xuất file: {str(e)}', 'danger')
        return redirect(url_for('revenue_report'))
    
    return send_file(output, 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name=f"Bao_cao_doanh_thu_{datetime.now().strftime('%Y%m%d')}.xlsx",
                     as_attachment=True)


@app.route('/admin/add-coupon', methods=['GET', 'POST'])
def add_coupon():
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    user = Admin.objects(email=session['email']).first()
    if request.method == 'POST':
        code = request.form.get('code').upper()
        discount_type = request.form.get('discount_type')
        discount_value = float(request.form.get('discount_value'))
        expiry_date_str = request.form.get('expiry_date')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        usage_limit = int(request.form.get('usage_limit', 100))
        
        if Coupon.objects(code=code).first():
            flash('Mã giảm giá này đã tồn tại!', 'danger')
            return redirect(url_for('add_coupon'))

        coupon = Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            expiry_date=expiry_date,
            usage_limit=usage_limit
        )
        coupon.save()
        flash('Thêm mã giảm giá thành công', 'success')
        return redirect(url_for('manage_coupons'))
    
    return render_template('admin/add_coupon.html', title='Thêm Mã giảm giá', user=user)


@app.route('/admin/delete-coupon/<string:id>')
def delete_coupon(id):
    if 'email' not in session:
        flash(f'Please login first', 'danger')
        return redirect(url_for('login'))
    coupon = Coupon.objects(id=id).first()
    if coupon:
        coupon.delete()
        flash('Đã xóa mã giảm giá', 'success')
    return redirect(url_for('manage_coupons'))

