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
from shop.recommender import get_content_based_recommendations, get_collaborative_recommendations
# 

# ===================================================================
#  HELPER
# ===================================================================

def brands():
    return Brand.objects().all()

def categories():
    desired_order = [
        "điện thoại thông minh",
        "máy tính xách tay",
        "đồng hồ thông minh",
        "tai nghe & âm thanh"
    ]
    cats = list(Category.objects().all())
    
    def sort_key(c):
        name_lower = c.name.lower().strip()
        if name_lower in desired_order:
            return desired_order.index(name_lower)
        # Nếu có danh mục nào khác thì xếp xuống cuối
        return 999
        
    cats.sort(key=sort_key)
    return cats

def registers():
    rated_users_ids = [rate.user_id for rate in Rate.objects().all()]
    return Register.objects(id__in=rated_users_ids).all()

def medium():
    """Tính điểm trung bình + số lượng đánh giá cho từng sản phẩm + phân bổ sao và chỉ số chi tiết."""
    products = Addproduct.objects(stock__gt=0).all()
    dst = {}
    for product in products:
        rates = Rate.objects(product=product).all()
        length = len(rates)
        
        star_dist = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        perf_sum, batt_sum, cam_sum = 0, 0, 0
        
        if length == 0:
            average = 5
            perf_avg, batt_avg, cam_avg = 5.0, 5.0, 5.0
        else:
            sum_value = 0
            for rate in rates:
                sum_value += rate.rate_number
                star_dist[rate.rate_number] = star_dist.get(rate.rate_number, 0) + 1
                perf_sum += getattr(rate, 'performance_rate', 5)
                batt_sum += getattr(rate, 'battery_rate', 5)
                cam_sum += getattr(rate, 'camera_rate', 5)
                
            average = sum_value / length
            perf_avg = perf_sum / length
            batt_avg = batt_sum / length
            cam_avg = cam_sum / length
            
        dst[product.id] = {
            'average': average,
            'count': length,
            'star_dist': star_dist,
            'experience': {
                'performance': round(perf_avg, 1),
                'battery': round(batt_avg, 1),
                'camera': round(cam_avg, 1)
            }
        }
    return dst


# ===================================================================
#  HOME
# ===================================================================

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    category = Category.objects(name="Điện thoại di động").first() # Thay đổi do mình setup DB mẫu theo tiếng việt

    # Nếu không tìm thấy dùng category đầu tiên
    cat_query = {'category': category} if category else {}

    products_all = Addproduct.objects(stock__gt=0, **cat_query).order_by('-id').paginate(page=page, per_page=4)
    products_hot = Addproduct.objects(stock__gt=0, **cat_query).order_by('-price').limit(3)
    products_new = Addproduct.objects(stock__gt=0, **cat_query).order_by('-id')
    products_sell = Addproduct.objects(stock__gt=0, discount__gt=0, **cat_query).order_by('-discount').limit(10)

    # --- AI Recommendation: Dành riêng cho bạn (Collaborative) ---
    ai_suggest = []
    if current_user.is_authenticated:
        ai_suggest = get_collaborative_recommendations(current_user.id, limit=4)
    # -------------------------------------------------------------

    avg_data = medium()
    top_rated_ids = [pid for pid, data in avg_data.items() if data['count'] > 0]
    top_rated_ids.sort(key=lambda pid: (avg_data[pid]['average'], avg_data[pid]['count']), reverse=True)
    
    top_rated_prods = []
    for pid in top_rated_ids[:6]:
        p = Addproduct.objects(id=pid, stock__gt=0).first()
        if p: top_rated_prods.append(p)
        
    if len(top_rated_prods) < 4:
        top_rated_prods = list(Addproduct.objects(stock__gt=0).order_by('-id').limit(6))

    products = {
        'all': products_all,
        'hot': products_hot,
        'new': products_new,
        'sell': products_sell,
        'average': avg_data,
        'ai_suggest': ai_suggest,
        'top_rated': top_rated_prods
    }

    return render_template(
        'customers/index.html',
        products=products,
        brands=brands(),
        categories=categories()
    )


@app.route('/load_more')
def load_more():
    page = request.args.get('page', 1, type=int)
    category = Category.objects(name="Điện thoại di động").first()
    cat_query = {'category': category} if category else {}
    
    products_all = Addproduct.objects(stock__gt=0, **cat_query).order_by('-id').paginate(page=page, per_page=4)
    
    html = render_template(
        'customers/_product_cards.html', 
        products_list=products_all.items,
        average_data=medium()
    )
    
    return {
        'html': html,
        'has_next': products_all.has_next
    }


# ===================================================================
#  CATEGORY PAGE (TẤT CẢ SẢN PHẨM)
# ===================================================================

@app.route('/category')
def get_all_category():
    """Trang liệt kê tất cả sản phẩm (dùng cho /category)."""
    page = request.args.get('page', 1, type=int)

    products_all = Addproduct.objects(stock__gt=0).order_by('-id').paginate(page=page, per_page=9)
    products_new = Addproduct.objects(stock__gt=0).order_by('-id').limit(2)

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
    get_cat = Category.objects(name=name).first()
    if not get_cat: return "Category not found", 404

    # Lấy sản phẩm thuộc category này, phân trang
    get_cat_prod_page = Addproduct.objects(category=get_cat).paginate(
        page=page,
        per_page=9
    )

    # Một vài sản phẩm mới để hiển thị bên cạnh
    products_new = Addproduct.objects(stock__gt=0).order_by('-id').limit(2)

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
        return redirect(url_for('unified_login'))

    if request.method == "POST":
        getbrand = request.form.get('brand')
        category_id = request.form.get('category') if request.form.get('category') else None
        
        try:
            category = Category.objects(id=category_id).first() if category_id else None
        except Exception:
            flash('Invalid category selected.', 'danger')
            return redirect(url_for('addbrand'))
        
        brand = Brand(name=getbrand, category=category)
        brand.save()
        flash(f'The brand {getbrand} was added to your database', 'success')
        return redirect(url_for('addbrand'))

    user = Admin.objects(email=session['email']).first()
    categories_list = Category.objects().all()
    return render_template(
        'products/addbrand.html',
        title='Add brand',
        categories=categories_list,
        user=user
    )


@app.route('/updatebrand/<string:id>', methods=['GET', 'POST'])
def updatebrand(id):
    if 'email' not in session:
        flash('Login first please', 'danger')
        return redirect(url_for('unified_login'))

    updatebrand_obj = Brand.objects(id=id).first()
    if not updatebrand_obj: return "Not found", 404
    brand_name = request.form.get('brand')

    if request.method == "POST":
        if brand_name:
            updatebrand_obj.name = brand_name
            updatebrand_obj.save()
            flash(f'The brand {updatebrand_obj.name} was updated', 'success')
        return redirect(url_for('brands'))    # endpoint /brands bên admin

    user = Admin.objects(email=session['email']).first()
    return render_template(
        'products/updatebrand.html',
        title='Update brand',
        updatebrand=updatebrand_obj,
        categories=categories(),
        user=user
    )


@app.route('/deletebrand/<string:id>', methods=['GET', 'POST'])
def deletebrand(id):
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('unified_login'))

    brand = Brand.objects(id=id).first()

    if request.method == "POST" and brand:
        # Xoá tất cả sản phẩm thuộc brand này + rate của chúng
        products = Addproduct.objects(brand=brand).all()
        for product in products:
            rates = Rate.objects(product=product).all()
            for rate in rates:
                rate.delete()
            product.delete()

        brand.delete()
        flash(f"The brand {brand.name} was deleted from your database", "success")
        return redirect(url_for('brands'))

    flash(f"The brand can't be deleted", "warning")
    return redirect(url_for('brands'))


# ===================================================================
#  ADD / UPDATE / DELETE CATEGORY
# ===================================================================

@app.route('/addcat', methods=['GET', 'POST'])
def addcat():
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('unified_login'))

    if request.method == "POST":
        getcat = request.form.get('category')
        cat = Category(name=getcat)
        cat.save()

        flash(f'The category {getcat} was added to your database', 'success')
        return redirect(url_for('addcat'))

    user = Admin.objects(email=session['email']).first()
    return render_template(
        'products/addbrand.html',
        title='Add category',
        user=user
    )


@app.route('/updatecat/<string:id>', methods=['GET', 'POST'])
def updatecat(id):
    if 'email' not in session:
        flash('Login first please', 'danger')
        return redirect(url_for('unified_login'))

    updatecat_obj = Category.objects(id=id).first()
    if not updatecat_obj: return "Not found", 404
    category_name = request.form.get('category')

    if request.method == "POST":
        if category_name:
            updatecat_obj.name = category_name
            updatecat_obj.save()
            flash(f'The category {updatecat_obj.name} was updated', 'success')
        return redirect(url_for('categories'))

    user = Admin.objects(email=session['email']).first()
    return render_template(
        'products/updatebrand.html',
        title='Update category',
        updatecat=updatecat_obj,
        user=user
    )


@app.route('/deletecat/<string:id>', methods=['GET', 'POST'])
def deletecat(id):
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('unified_login'))

    category_obj = Category.objects(id=id).first()

    if request.method == "POST" and category_obj:
        # Xoá toàn bộ product thuộc category + rate của chúng
        products = Addproduct.objects(category=category_obj).all()
        for product in products:
            rates = Rate.objects(product=product).all()
            for rate in rates:
                rate.delete()
            product.delete()

        # Xoá các brand thuộc category này
        brands_in_cat = Brand.objects(category=category_obj).all()
        for b in brands_in_cat:
            b.delete()

        category_obj.delete()
        flash(f"The category {category_obj.name} was deleted from your database", "success")
        return redirect(url_for('categories'))

    flash(f"The category can't be deleted", "warning")
    return redirect(url_for('categories'))


# ===================================================================
#  ADD PRODUCT
# ===================================================================

@app.route('/addproduct', methods=['GET', 'POST'])
def addproduct():
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('unified_login'))

    form = Addproducts(request.form)
    brands_list = Brand.objects().all()
    categories_list = Category.objects().all()

    if request.method == "POST":
        name = form.name.data
        price = float(form.price.data) if form.price.data else 0.0
        discount = form.discount.data
        stock = form.stock.data
        colors = form.colors.data
        capacity = form.capacity.data
        desc = form.description.data
        video_link = form.video_link.data
        review_video = form.review_video.data
        brand_id = request.form.get('brand')
        category_id = request.form.get('category')

        # GET FILES
        image_1 = request.files.get('image_1')
        image_2 = request.files.get('image_2')
        image_3 = request.files.get('image_3')
        image_4 = request.files.get('image_4')
        image_5 = request.files.get('image_5')

        import tempfile
        tmp_dir = tempfile.gettempdir()
        
        def process_image(img):
            if img and img.filename:
                ext = img.filename.split('.')[-1]
                name = secrets.token_hex(10) + "." + ext
                path = os.path.join(tmp_dir, name)
                img.save(path)
                try:
                    storage.child("images/" + name).put(path)
                except Exception as e:
                    print("Firebase Upload Error:", e)
                    raise Exception(f"Lỗi tải ảnh lên Firebase: {e}")
                finally:
                    if os.path.exists(path):
                        os.unlink(path)
                return name
            return ""

        try:
            name_1 = process_image(image_1)
            name_2 = process_image(image_2)
            name_3 = process_image(image_3)
            name_4 = process_image(image_4)
            name_5 = process_image(image_5)
        except Exception as e:
            flash(str(e), "danger")
            return redirect(url_for('addproduct'))

        # LƯU DB
        brand_ref = Brand.objects(id=brand_id).first() if brand_id else None
        cat_ref = Category.objects(id=category_id).first() if category_id else None

        product = Addproduct(
            name=name,
            price=price,
            discount=discount,
            stock=stock,
            colors=colors,
            capacity=capacity,
            desc=desc,
            video_link=video_link,
            review_video=review_video,
            category=cat_ref,
            brand=brand_ref,
            image_1=name_1,
            image_2=name_2,
            image_3=name_3,
            image_4=name_4,
            image_5=name_5
        )

        product.save()

        flash(f"The product {product.name} was added successfully.", "success")
        return redirect(url_for('addproduct'))

    user = Admin.objects(email=session['email']).first()

    return render_template(
        'products/addproduct.html',
        form=form,
        brands=brands_list,
        categories=categories_list,
        user=user
    )


# ===================================================================
#  UPDATE PRODUCT
# ===================================================================

@app.route('/updateproduct/<string:id>', methods=['GET', 'POST'])
def updateproduct(id):
    if 'email' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('unified_login'))

    form = Addproducts(request.form)
    product = Addproduct.objects(id=id).first()
    if not product: return "Not found", 404
    brands_list = Brand.objects().all()
    categories_list = Category.objects().all()

    brand_id = request.form.get('brand') if request.form.get('brand') else None
    category_id = request.form.get('category') if request.form.get('category') else None

    if request.method == "POST":
        product.name = form.name.data
        product.price = float(form.price.data) if form.price.data else 0.0
        product.discount = form.discount.data
        product.stock = form.stock.data
        product.colors = form.colors.data
        product.capacity = form.capacity.data
        product.desc = form.description.data
        product.video_link = form.video_link.data
        product.review_video = form.review_video.data
        if category_id: product.category = Category.objects(id=category_id).first()
        if brand_id: product.brand = Brand.objects(id=brand_id).first()

        import tempfile
        tmp_dir = tempfile.gettempdir()

        # Update images if provided
        if request.files.get('image_1'):
            image_1 = request.files.get('image_1')
            ext = image_1.filename.split('.')[-1]
            name_1 = secrets.token_hex(10) + "." + ext

            # Attempt to delete old file from Firebase (Optional, keeping it simple here)
            path1 = os.path.join(tmp_dir, name_1)
            image_1.save(path1)
            storage.child("images/" + name_1).put(path1)
            os.unlink(path1)
            product.image_1 = name_1

        if request.files.get('image_2'):
            image_2 = request.files.get('image_2')
            ext = image_2.filename.split('.')[-1]
            name_2 = secrets.token_hex(10) + "." + ext

            path2 = os.path.join(tmp_dir, name_2)
            image_2.save(path2)
            storage.child("images/" + name_2).put(path2)
            os.unlink(path2)
            product.image_2 = name_2

        if request.files.get('image_3'):
            image_3 = request.files.get('image_3')
            ext = image_3.filename.split('.')[-1]
            name_3 = secrets.token_hex(10) + "." + ext

            path3 = os.path.join(tmp_dir, name_3)
            image_3.save(path3)
            storage.child("images/" + name_3).put(path3)
            os.unlink(path3)
            product.image_3 = name_3

        if request.files.get('image_4'):
            image_4 = request.files.get('image_4')
            ext = image_4.filename.split('.')[-1]
            name_4 = secrets.token_hex(10) + "." + ext

            path4 = os.path.join(tmp_dir, name_4)
            image_4.save(path4)
            storage.child("images/" + name_4).put(path4)
            os.unlink(path4)
            product.image_4 = name_4

        if request.files.get('image_5'):
            image_5 = request.files.get('image_5')
            ext = image_5.filename.split('.')[-1]
            name_5 = secrets.token_hex(10) + "." + ext

            path5 = os.path.join(tmp_dir, name_5)
            image_5.save(path5)
            storage.child("images/" + name_5).put(path5)
            os.unlink(path5)
            product.image_5 = name_5

        product.save()
        flash('Product updated successfully', 'success')
        return redirect(url_for('product'))

    # Load existing data
    form.name.data = product.name
    form.price.data = product.price
    form.discount.data = product.discount
    form.stock.data = product.stock
    form.colors.data = product.colors
    form.capacity.data = product.capacity
    form.description.data = product.desc
    form.video_link.data = product.video_link
    form.review_video.data = product.review_video

    user = Admin.objects(email=session['email']).first()

    return render_template(
        'products/updateproduct.html',
        form=form,
        product=product,
        brands=brands_list,
        categories=categories_list,
        user=user
    )


# ===================================================================
#  DELETE PRODUCT
# ===================================================================

@app.route('/deleteproduct/<string:id>', methods=['POST'])
def deleteproduct(id):
    if 'email' not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login'))

    product = Addproduct.objects(id=id).first()
    if not product: return "Not found", 404

    try:
        storage.child("images/" + product.image_1).delete()
        storage.child("images/" + product.image_2).delete()
        storage.child("images/" + product.image_3).delete()
        if product.image_4:
            storage.child("images/" + product.image_4).delete()
        if product.image_5:
            storage.child("images/" + product.image_5).delete()
    except Exception as e:
        print("Firebase delete error:", e)

    rates = Rate.objects(product=product).all()
    for rate in rates:
        rate.delete()

    product.delete()

    flash(f"Product {product.name} deleted", "success")
    return redirect(url_for('product'))


# ===================================================================
#  DETAIL PRODUCT
# ===================================================================

@app.route('/detail/id_<string:id>')
def detail(id):
    kt = False
    customer = None
    if current_user.is_authenticated:
        customer = Register.objects(id=current_user.id).first()
        rates_all = Rate.objects().order_by('-id').all()
        for rate in rates_all:
            if rate.product and rate.product.id == id and rate.user_id == str(current_user.id):
                kt = True
                
    # --- AI Tracking: View Product (For both Auth and Guest) ---
    try:
        from .models import UserInteraction
        import uuid
        
        if current_user.is_authenticated:
            user_identifier = str(current_user.id)
        else:
            if not session.get('guest_id'):
                session['guest_id'] = str(uuid.uuid4())
            user_identifier = f"guest_{session['guest_id']}"
            
        # Prevent F5 spam: Check if this user/guest already viewed this product
        existing_view = UserInteraction.objects(
            user_id=user_identifier, 
            product_id=str(id), 
            interaction_type='view'
        ).first()
        
        if not existing_view:
            ui = UserInteraction(
                user_id=user_identifier, 
                product_id=str(id), 
                interaction_type='view', 
                weight=1
            )
            ui.save()
    except Exception as e:
        print("Error tracking view interaction:", e)
    # -----------------------------------------------------------

    form = Rates(request.form)
    
    product = Addproduct.objects(id=id).first()
    if not product: return "Not found", 404
    
    rates = Rate.objects(product=product).order_by('-id').all()
    
    # --- Link rates with user objects to show names ---
    rated_user_ids = [r.user_id for r in rates]
    users_map = {str(u.id): u for u in Register.objects(id__in=rated_user_ids).all()}
    for r in rates:
        r.register = users_map.get(r.user_id)
    # --------------------------------------------------
    products_hot = Addproduct.objects(stock__gt=0, category=product.category, id__ne=product.id).order_by('-price').limit(4)
    products_new = Addproduct.objects(stock__gt=0).order_by('-id').limit(2)
    products_sell = Addproduct.objects(stock__gt=0).order_by('-discount').limit(10)

    # --- AI Recommendation: Sản phẩm tương tự (Content-based) ---
    ai_suggest = get_content_based_recommendations(id, limit=4)
    
    # 1. Recently Viewed (Sản phẩm vừa xem)
    recently_viewed_ids = session.get('recently_viewed', [])
    if id not in recently_viewed_ids:
        recently_viewed_ids.insert(0, id)
    else:
        recently_viewed_ids.remove(id)
        recently_viewed_ids.insert(0, id)
    session['recently_viewed'] = recently_viewed_ids[:6]
    rv_products = Addproduct.objects(id__in=[i for i in recently_viewed_ids if i != id]).all()
    recently_viewed = sorted(rv_products, key=lambda x: recently_viewed_ids.index(str(x.id)))

    # 2. Frequently Bought Together (Mua cùng nhau - Phụ kiện)
    frequently_bought = []
    acc_cat = Category.objects(name__icontains="tai nghe").first()
    if not acc_cat:
        acc_cat = Category.objects(name__icontains="đồng hồ").first()
    if acc_cat and product.category != acc_cat:
        frequently_bought = Addproduct.objects(stock__gt=0, category=acc_cat).limit(4)

    # 3. Upsell (Nâng cấp đời máy)
    upsell = Addproduct.objects(stock__gt=0, category=product.category, price__gt=product.price).order_by('price').limit(4)

    from .models import UserInteraction
    all_suggested = list(products_hot) + list(ai_suggest) + list(recently_viewed) + list(frequently_bought) + list(upsell)
    view_counts = {}
    for p in set(all_suggested):
        view_counts[str(p.id)] = UserInteraction.objects(product_id=str(p.id), interaction_type='view').count()

    products = {
        'hot': products_hot, 
        'new': products_new, 
        'sell': products_sell, 
        'average': medium(),
        'ai_suggest': ai_suggest,
        'recently_viewed': recently_viewed,
        'frequently_bought': frequently_bought,
        'upsell': upsell,
        'view_counts': view_counts
    }

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
    search_value = f"{value.lower()}"
    page = request.args.get('page', 1, type=int)
    product = Addproduct.objects(name__icontains=search_value).paginate(page=page, per_page=9)

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
    brand_obj = Brand.objects(name=name).first()
    if not brand_obj: return "Brand not found", 404

    # Lấy các sản phẩm thuộc brand này, phân trang
    brand_products = Addproduct.objects(brand=brand_obj).paginate(
        page=page,
        per_page=9
    )

    # Lấy vài sản phẩm mới để hiển thị bên cạnh
    products_new = Addproduct.objects(stock__gt=0).order_by('-id').limit(2)

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
    product_discount = Addproduct.objects(
        stock__gt=0,
        discount__gte=start,
        discount__lt=end
    ).order_by('-id').paginate(page=page, per_page=9)

    # Một vài sản phẩm mới để hiển thị bên cạnh
    products_new = Addproduct.objects(stock__gt=0).order_by('-id').limit(2)

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

    product_obj = Addproduct.objects(id=product_id).first()
    if not product_obj: return redirect(url_for('home'))

    # lưu đánh giá
    rate = Rate(
        user_id=register_id,
        product=product_obj,
        desc=desc,
        rate_number=int(rate_number),
        performance_rate=int(request.form.get('performance_rate', 5)),
        battery_rate=int(request.form.get('battery_rate', 5)),
        camera_rate=int(request.form.get('camera_rate', 5))
    )
    rate.save()

    flash("Thank you for your rating!", "success")
    return redirect(url_for('detail', id=product_id))
