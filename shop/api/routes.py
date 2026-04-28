# -*- coding: utf-8 -*-
"""
============================================================
  GIAI ĐOẠN 5: REST API Layer
  
  Cung cấp toàn bộ dữ liệu dưới dạng JSON cho React Frontend.
  Tất cả các endpoint đều có prefix /api/v1/
  
  LƯU Ý: Các endpoint này SONG SONG với các route Jinja2 cũ.
  Hệ thống cũ vẫn hoạt động bình thường, React frontend
  chỉ gọi đến các API này khi được bật.
============================================================
"""
from flask import jsonify, request, session
from flask_login import current_user, login_required

from shop import app, cache
from shop.products.models import Addproduct, Category, Brand, Rate, UserInteraction
from shop.customers.models import Register, CustomerOrder
from shop.recommender import (
    get_content_based_recommendations,
    get_collaborative_recommendations,
    get_fallback_recommendations,
)


# ======================================================================
#  HELPER: Chuyển MongoEngine Document thành dict
# ======================================================================
def _product_to_dict(p):
    """Serialize 1 sản phẩm thành JSON-safe dict."""
    return {
        'id': str(p.id),
        'name': p.name,
        'price': float(p.price),
        'discount': int(p.discount) if p.discount else 0,
        'final_price': float(p.price - p.price * (p.discount or 0) / 100),
        'stock': int(p.stock) if p.stock else 0,
        'desc': p.desc or '',
        'colors': p.colors or '',
        'capacity': getattr(p, 'capacity', '') or '',
        'image_1': p.image_1 or '',
        'image_2': p.image_2 or '',
        'image_3': p.image_3 or '',
        'category': {
            'id': str(p.category.id),
            'name': p.category.name
        } if p.category else None,
        'brand': {
            'id': str(p.brand.id),
            'name': p.brand.name
        } if p.brand else None,
    }


def _category_to_dict(c):
    return {'id': str(c.id), 'name': c.name}


def _brand_to_dict(b):
    return {
        'id': str(b.id),
        'name': b.name,
        'category_id': str(b.category_id.id) if b.category_id else None,
    }


# ======================================================================
#  API: Products
# ======================================================================
@app.route('/api/v1/products', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def api_products():
    """Lấy danh sách sản phẩm với phân trang và bộ lọc."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category = request.args.get('category', None)
    brand = request.args.get('brand', None)
    search = request.args.get('q', None)
    sort = request.args.get('sort', '-id')  # -id, price, -price, -discount

    query = {}
    if category:
        cat_obj = Category.objects(name=category).first()
        if cat_obj:
            query['category'] = cat_obj
    if brand:
        brand_obj = Brand.objects(name=brand).first()
        if brand_obj:
            query['brand'] = brand_obj
    if search:
        query['name__icontains'] = search

    products_qs = Addproduct.objects(**query).order_by(sort)
    total = products_qs.count()

    # Manual pagination
    start = (page - 1) * per_page
    items = products_qs[start:start + per_page]

    return jsonify({
        'status': 'success',
        'data': [_product_to_dict(p) for p in items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })


@app.route('/api/v1/products/<string:product_id>', methods=['GET'])
@cache.cached(timeout=120)
def api_product_detail(product_id):
    """Chi tiết 1 sản phẩm."""
    product = Addproduct.objects(id=product_id).first()
    if not product:
        return jsonify({'status': 'error', 'message': 'Product not found'}), 404

    # Lấy đánh giá
    rates = Rate.objects(product=product).order_by('-id')
    reviews = []
    for r in rates:
        reviews.append({
            'user': r.register.username if r.register else 'Ẩn danh',
            'rating': r.rate_number,
            'comment': r.desc or '',
            'time': str(r.time) if r.time else '',
        })

    data = _product_to_dict(product)
    data['reviews'] = reviews

    return jsonify({'status': 'success', 'data': data})


# ======================================================================
#  API: Categories & Brands
# ======================================================================
@app.route('/api/v1/categories', methods=['GET'])
@cache.cached(timeout=300)
def api_categories():
    cats = Category.objects().order_by('name').all()
    return jsonify({
        'status': 'success',
        'data': [_category_to_dict(c) for c in cats]
    })


@app.route('/api/v1/brands', methods=['GET'])
@cache.cached(timeout=300)
def api_brands():
    category = request.args.get('category', None)
    if category:
        cat_obj = Category.objects(name=category).first()
        brands_qs = Brand.objects(category_id=cat_obj).all() if cat_obj else []
    else:
        brands_qs = Brand.objects().order_by('name').all()
    return jsonify({
        'status': 'success',
        'data': [_brand_to_dict(b) for b in brands_qs]
    })


# ======================================================================
#  API: AI Recommendations
# ======================================================================
@app.route('/api/v1/recommendations/personal', methods=['GET'])
def api_recommendations_personal():
    """Gợi ý cá nhân hóa (Collaborative Filtering)."""
    limit = request.args.get('limit', 4, type=int)
    if current_user.is_authenticated:
        items = get_collaborative_recommendations(current_user.id, limit=limit)
    else:
        items = get_fallback_recommendations(limit=limit)
    return jsonify({
        'status': 'success',
        'type': 'collaborative' if current_user.is_authenticated else 'fallback',
        'data': [_product_to_dict(p) for p in items]
    })


@app.route('/api/v1/recommendations/similar/<string:product_id>', methods=['GET'])
@cache.cached(timeout=120)
def api_recommendations_similar(product_id):
    """Gợi ý sản phẩm tương tự (Content-based)."""
    limit = request.args.get('limit', 4, type=int)
    items = get_content_based_recommendations(product_id, limit=limit)
    return jsonify({
        'status': 'success',
        'type': 'content_based',
        'data': [_product_to_dict(p) for p in items]
    })


# ======================================================================
#  API: Cart (JSON Interface)
# ======================================================================
@app.route('/api/v1/cart', methods=['GET'])
def api_get_cart():
    """Lấy giỏ hàng hiện tại."""
    cart = session.get('Shoppingcart', {})
    items = []
    subtotal = 0
    discount_total = 0

    for key, product in cart.items():
        price = float(product['price'])
        qty = int(product['quantity'])
        discount = int(product.get('discount', 0))
        item_total = price * qty
        item_discount = item_total * discount / 100

        items.append({
            'product_id': key,
            'name': product.get('name', ''),
            'price': price,
            'quantity': qty,
            'discount': discount,
            'color': product.get('color', ''),
            'capacity': product.get('capacity', ''),
            'image': product.get('image', ''),
            'subtotal': item_total,
            'discount_amount': item_discount,
            'final_total': item_total - item_discount,
        })
        subtotal += item_total
        discount_total += item_discount

    return jsonify({
        'status': 'success',
        'data': {
            'items': items,
            'subtotal': subtotal,
            'discount_total': discount_total,
            'grand_total': subtotal - discount_total,
            'item_count': len(items)
        }
    })


# ======================================================================
#  API: User / Auth Status
# ======================================================================
@app.route('/api/v1/auth/status', methods=['GET'])
def api_auth_status():
    """Kiểm tra trạng thái đăng nhập."""
    if current_user.is_authenticated:
        return jsonify({
            'status': 'success',
            'authenticated': True,
            'user': {
                'id': str(current_user.id),
                'username': current_user.username,
                'email': current_user.email,
            }
        })
    return jsonify({
        'status': 'success',
        'authenticated': False,
        'user': None
    })


# ======================================================================
#  API: AI Dashboard Stats (cho Admin - Giai đoạn 6)
# ======================================================================
@app.route('/api/v1/admin/ai-stats', methods=['GET'])
def api_ai_stats():
    """Thống kê hiệu quả hệ thống AI cho Admin Dashboard."""
    if 'email' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        # Tổng số tương tác
        total_interactions = UserInteraction.objects().count()

        # Phân bố theo loại
        view_count = UserInteraction.objects(interaction_type='view').count()
        cart_count = UserInteraction.objects(interaction_type='cart').count()
        purchase_count = UserInteraction.objects(interaction_type='purchase').count()

        # Số user unique đã tương tác
        unique_users = len(UserInteraction.objects().distinct('user_id'))

        # Top 10 sản phẩm được xem nhiều nhất
        pipeline = [
            {'$group': {'_id': '$product_id', 'total_weight': {'$sum': '$weight'}, 'count': {'$sum': 1}}},
            {'$sort': {'total_weight': -1}},
            {'$limit': 10}
        ]
        top_products_raw = list(UserInteraction.objects().aggregate(pipeline))

        top_products = []
        for item in top_products_raw:
            product = Addproduct.objects(id=item['_id']).first()
            top_products.append({
                'product_id': str(item['_id']),
                'product_name': product.name if product else 'Đã xóa',
                'total_score': item['total_weight'],
                'interaction_count': item['count'],
            })

        # Conversion funnel: View -> Cart -> Purchase
        conversion_rate = 0
        if view_count > 0:
            conversion_rate = round((purchase_count / view_count) * 100, 2)

        cart_rate = 0
        if view_count > 0:
            cart_rate = round((cart_count / view_count) * 100, 2)

        return jsonify({
            'status': 'success',
            'data': {
                'total_interactions': total_interactions,
                'interaction_breakdown': {
                    'views': view_count,
                    'cart_adds': cart_count,
                    'purchases': purchase_count,
                },
                'unique_users': unique_users,
                'conversion_funnel': {
                    'view_to_cart_rate': cart_rate,
                    'view_to_purchase_rate': conversion_rate,
                },
                'top_products': top_products,
                'total_products': Addproduct.objects().count(),
                'total_customers': Register.objects().count(),
                'total_orders': CustomerOrder.objects(status__ne=None).count(),
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/admin/ai-reset', methods=['POST'])
def api_ai_reset():
    """Xóa toàn bộ dữ liệu tương tác để reset AI Dashboard."""
    if 'email' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        # Xóa toàn bộ tương tác người dùng
        UserInteraction.objects().delete()
        
        return jsonify({
            'status': 'success',
            'message': 'Đã reset toàn bộ dữ liệu tương tác AI thành công.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
