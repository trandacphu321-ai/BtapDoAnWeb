import urllib
import os
import secrets

from flask import (
    render_template, session, request, redirect,
    url_for, flash, current_app
)
from flask_login import login_required, current_user

from shop import app, db, photos, storage
from .models import Category, Brand, Addproduct, Rate, Register
from .forms import Addproducts, Rates
from shop.admin.models import Admin
# 

# ===================================================================
#  HELPER
# ===================================================================

def brands():
    return Brand.query.all()


def categories():
    return Category.query.order_by(Category.name.desc()).all()


def registers():
    return Register.query.join(Rate, (Register.id == Rate.register_id)).all()


def medium():
    """Tính điểm trung bình + số lượng đánh giá cho từng sản phẩm."""
    products = Addproduct.query.filter(Addproduct.stock > 0).all()
    dst = {}
    for product in products:
        rates = Rate.query.filter(Rate.product_id == product.id).all()
        length = len(rates)
        if length == 0:
            average = 5
        else:
            sum_value = sum(rate.rate_number for rate in rates)
            average = sum_value / length
        dst[product.id] = [average, length]
    return dst


# ===================================================================
#  HOME
# ===================================================================

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    category = Category.query.filter_by(name="Smartphone").first()

    products_all = Addproduct.query.filter(
        Addproduct.stock > 0,
        Addproduct.category_id == category.id
    ).order_by(Addproduct.id.desc()).paginate(page=page, per_page=4)

    products_hot = Addproduct.query.filter(
        Addproduct.stock > 0,
        Addproduct.category_id == category.id
    ).order_by(Addproduct.price.desc()).limit(3).all()

    products_new = Addproduct.query.filter(
        Addproduct.stock > 0,
        Addproduct.category_id == category.id
    ).order_by(Addproduct.id.desc()).all()

    products_sell = Addproduct.query.filter(
        Addproduct.stock > 0,
        Addproduct.category_id == category.id
    ).order_by(Addproduct.discount.desc()).limit(10).all()

    products = {
        'all': products_all,
        'hot': products_hot,
        'new': products_new,
        'sell': products_sell,
        'average': medium()
    }

    return render_template(
        'customers/index.html',
        products=products,
        brands=brands(),
        categories=categories()
    )


# ===================================================================
#  CATEGORY PAGE (TẤT CẢ SẢN PHẨM)
# ===================================================================

@app.route('/category')
def get_all_category():
    """Trang liệt kê tất cả sản phẩm (dùng cho /category)."""
    page = request.args.get('page', 1, type=int)

    products_all = Addproduct.query.filter(
        Addproduct.stock > 0
    ).order_by(Addproduct.id.desc()).paginate(page=page, per_page=9)

    products_new = Addproduct.query.filter(
        Addproduct.stock > 0
    ).order_by(Addproduct.id.desc()).limit(2).all()

    products = {
        'all': products_all,
        'new': products_new,
        'average': medium()
    }

    return render_template(
        'products/category.html',
        products=products,
        brands=brands(),
        categories=categories()
    )


# ===================================================================
#  CATEGORY PAGE THEO TÊN (CHO HEADER MENU)
# ===================================================================

@app.route('/categories/<string:name>')
def get_category(name):
    """Trang liệt kê sản phẩm theo từng category (theo tên)."""
    page = request.args.get('page', 1, type=int)

    # Lấy category theo tên, nếu không thấy thì 404
    get_cat = Category.query.filter_by(name=name).first_or_404()

    # Lấy sản phẩm thuộc category này, phân trang
    get_cat_prod_page = Addproduct.query.filter_by(category=get_cat).paginate(
        page=page,
        per_page=9
    )

    # Một vài sản phẩm mới để hiển thị bên cạnh
    products_new = Addproduct.query.filter(
        Addproduct.stock > 0
    ).order_by(Addproduct.id.desc()).limit(2).all()

    products = {
        'all': get_cat_prod_page,
        'new': products_new,
        'average': medium()
    }

    # Thông tin category truyền sang template giữ giống code cũ
    get_cat_info = {'name': name, 'id': get_cat.id}

    return render_template(
        'products/category.html',
        products=products,
        get_cat_prod=get_cat_info,
        brands=brands(),
        categories=categories(),
        get_cat=get_cat
    )


# ===================================================================
#  ADD / UPDATE / DELETE BRAND
# ===================================================================

@app.route('/addbrand', methods=['GET', 'POST'])
def addbrand():
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":
        getbrand = request.form.get('brand')
        category = request.form.get('category')
        brand = Brand(name=getbrand, category_id=category)
        db.session.add(brand)
        db.session.commit()
        flash(f'The brand {getbrand} was added to your database', 'success')
        return redirect(url_for('addbrand'))

    user = Admin.query.filter_by(email=session['email']).all()
    categories_list = Category.query.all()
    return render_template(
        'products/addbrand.html',
        title='Add brand',
        categories=categories_list,
        user=user[0]
    )


@app.route('/updatebrand/<int:id>', methods=['GET', 'POST'])
def updatebrand(id):
    if 'email' not in session:
        flash('Login first please', 'danger')
        return redirect(url_for('login'))

    updatebrand_obj = Brand.query.get_or_404(id)
    brand_name = request.form.get('brand')

    if request.method == "POST":
        if brand_name:
            updatebrand_obj.name = brand_name
            db.session.commit()
            flash(f'The brand {updatebrand_obj.name} was updated', 'success')
        return redirect(url_for('brands'))    # endpoint /brands bên admin

    user = Admin.query.filter_by(email=session['email']).all()
    return render_template(
        'products/updatebrand.html',
        title='Update brand',
        updatebrand=updatebrand_obj,
        categories=categories(),
        user=user[0]
    )


@app.route('/deletebrand/<int:id>', methods=['GET', 'POST'])
def deletebrand(id):
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    brand = Brand.query.get_or_404(id)

    if request.method == "POST":
        # Xoá tất cả sản phẩm thuộc brand này + rate của chúng
        products = Addproduct.query.filter(Addproduct.brand_id == id).all()
        for product in products:
            rates = Rate.query.filter(Rate.product_id == product.id).all()
            for rate in rates:
                db.session.delete(rate)
            db.session.delete(product)

        db.session.delete(brand)
        db.session.commit()
        flash(f"The brand {brand.name} was deleted from your database", "success")
        return redirect(url_for('brands'))

    flash(f"The brand {brand.name} can't be deleted from your database", "warning")
    return redirect(url_for('brands'))


# ===================================================================
#  ADD / UPDATE / DELETE CATEGORY
# ===================================================================

@app.route('/addcat', methods=['GET', 'POST'])
def addcat():
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":
        getcat = request.form.get('category')
        cat = Category(name=getcat)
        db.session.add(cat)
        db.session.commit()

        flash(f'The category {getcat} was added to your database', 'success')
        return redirect(url_for('addcat'))

    user = Admin.query.filter_by(email=session['email']).all()
    return render_template(
        'products/addbrand.html',
        title='Add category',
        user=user[0]
    )


@app.route('/updatecat/<int:id>', methods=['GET', 'POST'])
def updatecat(id):
    if 'email' not in session:
        flash('Login first please', 'danger')
        return redirect(url_for('login'))

    updatecat_obj = Category.query.get_or_404(id)
    category_name = request.form.get('category')

    if request.method == "POST":
        if category_name:
            updatecat_obj.name = category_name
            db.session.commit()
            flash(f'The category {updatecat_obj.name} was updated', 'success')
        return redirect(url_for('categories'))

    user = Admin.query.filter_by(email=session['email']).all()
    return render_template(
        'products/updatebrand.html',
        title='Update category',
        updatecat=updatecat_obj,
        user=user[0]
    )


@app.route('/deletecat/<int:id>', methods=['GET', 'POST'])
def deletecat(id):
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    category_obj = Category.query.get_or_404(id)

    if request.method == "POST":
        # Xoá toàn bộ product thuộc category + rate của chúng
        products = Addproduct.query.filter(Addproduct.category_id == id).all()
        for product in products:
            rates = Rate.query.filter(Rate.product_id == product.id).all()
            for rate in rates:
                db.session.delete(rate)
            db.session.delete(product)

        # Xoá các brand thuộc category này
        brands_in_cat = Brand.query.filter(Brand.category_id == id).all()
        for b in brands_in_cat:
            db.session.delete(b)

        db.session.delete(category_obj)
        db.session.commit()
        flash(f"The category {category_obj.name} was deleted from your database", "success")
        return redirect(url_for('categories'))

    flash(f"The category {category_obj.name} can't be deleted from your database", "warning")
    return redirect(url_for('categories'))


# ===================================================================
#  ADD PRODUCT
# ===================================================================

@app.route('/addproduct', methods=['GET', 'POST'])
def addproduct():
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    form = Addproducts(request.form)
    brands_list = Brand.query.all()
    categories_list = Category.query.all()

    if request.method == "POST":
        name = form.name.data
        price = form.price.data
        discount = form.discount.data
        stock = form.stock.data
        colors = form.colors.data
        desc = form.description.data
        brand = request.form.get('brand')
        category = request.form.get('category')

        # GET FILES
        image_1 = request.files.get('image_1')
        image_2 = request.files.get('image_2')
        image_3 = request.files.get('image_3')

        # RANDOM NAMES (tên file lưu thật)
        name_1 = secrets.token_hex(10) + "." + image_1.filename.split('.')[-1]
        name_2 = secrets.token_hex(10) + "." + image_2.filename.split('.')[-1]
        name_3 = secrets.token_hex(10) + "." + image_3.filename.split('.')[-1]

        # PATH SAVE
        path1 = os.path.join(current_app.root_path, "static/images", name_1)
        path2 = os.path.join(current_app.root_path, "static/images", name_2)
        path3 = os.path.join(current_app.root_path, "static/images", name_3)

        # SAVE FILE
        image_1.save(path1)
        image_2.save(path2)
        image_3.save(path3)

        # UPLOAD TO FIREBASE
        storage.child("images/" + name_1).put(path1)
        storage.child("images/" + name_2).put(path2)
        storage.child("images/" + name_3).put(path3)

        # LƯU DB
        product = Addproduct(
            name=name,
            price=price,
            discount=discount,
            stock=stock,
            colors=colors,
            desc=desc,
            category_id=category,
            brand_id=brand,
            image_1=name_1,
            image_2=name_2,
            image_3=name_3
        )

        db.session.add(product)
        db.session.commit()

        flash(f"The product {product.name} was added successfully.", "success")
        return redirect(url_for('addproduct'))

    user = Admin.query.filter_by(email=session['email']).all()

    return render_template(
        'products/addproduct.html',
        form=form,
        brands=brands_list,
        categories=categories_list,
        user=user[0]
    )


# ===================================================================
#  UPDATE PRODUCT
# ===================================================================

@app.route('/updateproduct/<int:id>', methods=['GET', 'POST'])
def updateproduct(id):
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    form = Addproducts(request.form)
    product = Addproduct.query.get_or_404(id)
    brands_list = Brand.query.all()
    categories_list = Category.query.all()

    brand = request.form.get('brand')
    category = request.form.get('category')

    if request.method == "POST":
        product.name = form.name.data
        product.price = form.price.data
        product.discount = form.discount.data
        product.stock = form.stock.data
        product.colors = form.colors.data
        product.desc = form.description.data
        product.category_id = category
        product.brand_id = brand

        # Update images if provided
        if request.files.get('image_1'):
            image_1 = request.files.get('image_1')
            ext = image_1.filename.split('.')[-1]
            name_1 = secrets.token_hex(10) + "." + ext

            try:
                os.unlink(os.path.join(current_app.root_path, "static/images", product.image_1))
            except Exception:
                pass

            photos.save(image_1, name=name_1)
            product.image_1 = name_1
            storage.child("images/" + name_1).put(
                os.path.join(current_app.root_path, "static/images", name_1)
            )

        if request.files.get('image_2'):
            image_2 = request.files.get('image_2')
            ext = image_2.filename.split('.')[-1]
            name_2 = secrets.token_hex(10) + "." + ext

            try:
                os.unlink(os.path.join(current_app.root_path, "static/images", product.image_2))
            except Exception:
                pass

            photos.save(image_2, name=name_2)
            product.image_2 = name_2
            storage.child("images/" + name_2).put(
                os.path.join(current_app.root_path, "static/images", name_2)
            )

        if request.files.get('image_3'):
            image_3 = request.files.get('image_3')
            ext = image_3.filename.split('.')[-1]
            name_3 = secrets.token_hex(10) + "." + ext

            try:
                os.unlink(os.path.join(current_app.root_path, "static/images", product.image_3))
            except Exception:
                pass

            photos.save(image_3, name=name_3)
            product.image_3 = name_3
            storage.child("images/" + name_3).put(
                os.path.join(current_app.root_path, "static/images", name_3)
            )

        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('product'))

    # Load existing data
    form.name.data = product.name
    form.price.data = product.price
    form.discount.data = product.discount
    form.stock.data = product.stock
    form.colors.data = product.colors
    form.description.data = product.desc

    user = Admin.query.filter_by(email=session['email']).all()

    return render_template(
        'products/updateproduct.html',
        form=form,
        product=product,
        brands=brands_list,
        categories=categories_list,
        user=user[0]
    )


# ===================================================================
#  DELETE PRODUCT
# ===================================================================

@app.route('/deleteproduct/<int:id>', methods=['POST'])
def deleteproduct(id):
    if 'email' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    product = Addproduct.query.get_or_404(id)

    try:
        os.unlink(os.path.join(current_app.root_path, "static/images", product.image_1))
        os.unlink(os.path.join(current_app.root_path, "static/images", product.image_2))
        os.unlink(os.path.join(current_app.root_path, "static/images", product.image_3))
    except Exception:
        pass

    rates = Rate.query.filter(Rate.product_id == id).all()
    for rate in rates:
        db.session.delete(rate)

    db.session.delete(product)
    db.session.commit()

    flash(f"Product {product.name} deleted", "success")
    return redirect(url_for('product'))


# ===================================================================
#  DETAIL PRODUCT
# ===================================================================

@app.route('/detail/id_<int:id>')
def detail(id):
    kt = False
    customer = None
    if current_user.is_authenticated:
        customer = Register.query.get_or_404(current_user.id)
        rates_all = Rate.query.order_by(Rate.id.desc()).all()
        for rate in rates_all:
            if id == rate.product_id and customer.id == rate.register_id:
                kt = True

    form = Rates(request.form)
    rates = Rate.query.filter(Rate.product_id == id).order_by(Rate.id.desc()).all()
    products_hot = Addproduct.query.filter(Addproduct.stock > 0).order_by(Addproduct.price.desc()).limit(3).all()
    products_new = Addproduct.query.filter(Addproduct.stock > 0).order_by(Addproduct.id.desc()).limit(2).all()
    products_sell = Addproduct.query.filter(Addproduct.stock > 0).order_by(Addproduct.discount.desc()).limit(10).all()

    products = {'hot': products_hot, 'new': products_new, 'sell': products_sell, 'average': medium()}
    product = Addproduct.query.get_or_404(id)

    return render_template(
        'products/product.html',
        product=product,
        products=products,
        form=form,
        rates=rates,
        registers=registers(),
        brands=brands(),
        categories=categories(),
        customer=customer,
        kt=kt
    )


# ===================================================================
#  SEARCH
# ===================================================================

@app.route('/search', methods=['GET', 'POST'])
def search():
    value = request.form['search']
    search_value = f"%{value.lower()}%"
    page = request.args.get('page', 1, type=int)
    product = Addproduct.query.filter(
        Addproduct.name.ilike(search_value)
    ).paginate(page=page, per_page=9)

    products = {'all': product, 'average': medium()}
    return render_template(
        'products/category.html',
        get_search=value,
        products=products,
        brands=brands(),
        categories=categories()
    )


# ===================================================================
#  PRODUCTS BY BRAND
# ===================================================================

@app.route('/category/brand/<string:name>')
def get_brand(name):
    page = request.args.get('page', 1, type=int)

    # Lấy đối tượng Brand theo tên, nếu không có thì 404
    brand_obj = Brand.query.filter_by(name=name).first_or_404()

    # Lấy các sản phẩm thuộc brand này, phân trang
    brand_products = Addproduct.query.filter_by(brand=brand_obj).paginate(
        page=page,
        per_page=9
    )

    # Lấy vài sản phẩm mới để hiển thị bên cạnh
    products_new = Addproduct.query.filter(
        Addproduct.stock > 0
    ).order_by(Addproduct.id.desc()).limit(2).all()

    products = {
        'all': brand_products,
        'new': products_new,
        'average': medium()
    }

    return render_template(
        'products/category.html',
        products=products,
        brand=name,
        brands=brands(),
        categories=categories(),
        get_brand=brand_obj
    )
# ===================================================================
#  PRODUCTS BY DISCOUNT (lọc theo % giảm giá)
# ===================================================================

@app.route('/category/discount/<int:start>-<int:end>')
def get_discount(start, end):
    page = request.args.get('page', 1, type=int)

    # Lọc sản phẩm theo khoảng phần trăm giảm giá
    product_discount = Addproduct.query.filter(
        Addproduct.stock > 0,
        Addproduct.discount >= start,
        Addproduct.discount < end
    ).order_by(Addproduct.id.desc()).paginate(page=page, per_page=9)

    # Một vài sản phẩm mới để hiển thị bên cạnh
    products_new = Addproduct.query.filter(
        Addproduct.stock > 0
    ).order_by(Addproduct.id.desc()).limit(2).all()

    products = {
        'all': product_discount,
        'new': products_new,
        'average': medium()
    }

    return render_template(
        'products/category.html',
        products=products,
        brands=brands(),
        categories=categories()
    )
# ===================================================================
#  ADD RATE (ĐÁNH GIÁ SẢN PHẨM)
# ===================================================================
@app.route('/addrate', methods=['POST'])
def addrate():
    # form = Rates(request.form)  # nếu cần dùng WTForms thì giữ lại

    register_id = request.form.get('register_id')
    product_id  = request.form.get('product_id')
    desc        = request.form.get('desc')
    rate_number = request.form.get('select')  # tên name trong <select>

    if not (register_id and product_id and rate_number):
        flash("Invalid rating data", "danger")
        # nếu thiếu product_id thì quay về trang chủ cho an toàn
        if product_id:
            return redirect(url_for('detail', id=product_id))
        return redirect(url_for('home'))

    # lưu đánh giá
    rate = Rate(
        register_id=register_id,
        product_id=product_id,
        desc=desc,
        rate_number=rate_number
    )
    db.session.add(rate)
    db.session.commit()

    flash("Thank you for your rating!", "success")
    return redirect(url_for('detail', id=product_id))
