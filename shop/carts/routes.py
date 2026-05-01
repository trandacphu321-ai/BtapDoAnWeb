import secrets

from flask import render_template, session, request, redirect, url_for, flash, current_app
from flask_login import current_user

from shop import db, app
from shop.customers.models import CustomerOrder
from shop.products.models import Category, Brand, Addproduct
from shop.products.routes import brands, categories
import json


def brands():
    brands = Brand.objects().all()
    return brands


def categories():
    categories = Category.objects().order_by('-name').all()
    return categories


def MagerDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))


@app.route('/addcart', methods=['POST'])
def AddCart():
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        color = request.form.get('colors')
        capacity = request.form.get('capacity', '') # Get capacity from form
        product = Addproduct.objects(id=product_id).first()
        brand = product.brand.name if product and product.brand else ''
        
        # Calculate dynamic price based on capacity
        selected_price = float(product.price)
        is_flash = product.is_flash_active
        
        if is_flash:
            selected_price = product.flash_price
        elif capacity and getattr(product, 'capacity', None):
            caps = product.capacity.split(',')
            for c in caps:
                parts = c.split(':')
                if parts[0].strip() == capacity and len(parts) > 1:
                    try:
                        selected_price = float(parts[1].strip())
                    except ValueError:
                        pass
                    break

        if request.method == "POST":
            # --- AI Tracking: Cart Product ---
            if current_user.is_authenticated:
                try:
                    from shop.products.models import UserInteraction
                    ui = UserInteraction(
                        user_id=str(current_user.id), 
                        product_id=str(product_id), 
                        interaction_type='cart', 
                        weight=3
                    )
                    ui.save()
                except Exception as e:
                    print("Error tracking cart interaction:", e)
            # ---------------------------------
            # if product_id in orders
            DictItems = {str(product_id): {'name': product.name, 'price': selected_price, 'discount': product.discount,
                                      'color': color, 'capacity': capacity, 'quantity': quantity, 'image': product.image_1,
                                      'colors': product.colors, 'capacities': getattr(product, 'capacity', ''), 'brand': brand}}
            if 'Shoppingcart' in session:
                # print(session['Shoppingcart'])
                if str(product_id) in session['Shoppingcart']:
                    for key, item in session['Shoppingcart'].items():
                        if str(key) == str(product_id):
                            session.modified = True
                            item['quantity'] += quantity;
                            if current_user.is_authenticated:
                                current_user.cart = session['Shoppingcart']
                                current_user.save()
                else:
                    session['Shoppingcart'] = MagerDicts(session['Shoppingcart'], DictItems)
                    if current_user.is_authenticated:
                        current_user.cart = session['Shoppingcart']
                        current_user.save()
                    return redirect(request.referrer)
            else:
                session['Shoppingcart'] = DictItems
                if current_user.is_authenticated:
                    current_user.cart = session['Shoppingcart']
                    current_user.save()

                return redirect(request.referrer)

    except Exception as e:
        print("Loi", e)
    
    return redirect(request.referrer)


@app.route('/carts')
def getCart():
    # Giỏ trống
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) == 0:
        return render_template(
            'products/carts.html',
            empty=True,
            brands=brands(),
            categories=categories(),
            subtotals=0,
            discounttotal=0
        )

    # Giỏ có hàng
    cart = session['Shoppingcart']
    subtotals = 0
    discounttotal = 0
    for key, product in cart.items():
        price = float(product['price'])
        qty = int(product['quantity'])
        discount = int(product.get('discount', 0))

        subtotals += price * qty
        discounttotal += price * qty * discount / 100

    return render_template(
        'products/carts.html',
        empty=False,
        brands=brands(),
        categories=categories(),
        subtotals=subtotals,
        discounttotal=discounttotal
    )


@app.route('/updatecart/<string:code>', methods=['POST'])
def updatecart(code):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('getCart'))
    if request.method == "POST":
        quantity = request.form.get('quantity')
        color = request.form.get('color')
        capacity = request.form.get('capacity', '')
        try:
            session.modified = True
            for key, item in session['Shoppingcart'].items():
                if str(key) == str(code):
                    item['quantity'] = quantity
                    item['color'] = color
                    item['capacity'] = capacity
                    
                    # Update price based on new capacity
                    product_obj = Addproduct.objects(id=code).first()
                    new_price = float(product_obj.price)
                    if product_obj.is_flash_active:
                        new_price = product_obj.flash_price
                    elif capacity and getattr(product_obj, 'capacity', None):
                        # Nếu capacity gửi lên có chứa giá (vd: "512GB:29000000")
                        selected_cap_name = capacity.split(':')[0].strip() if ':' in capacity else capacity.strip()
                        
                        caps = product_obj.capacity.split(',')
                        for c in caps:
                            parts = c.split(':')
                            if parts[0].strip() == selected_cap_name and len(parts) > 1:
                                try:
                                    new_price = float(parts[1].strip())
                                except ValueError:
                                    pass
                                break
                    item['price'] = new_price
                    if current_user.is_authenticated:
                        current_user.cart = session['Shoppingcart']
                        current_user.save()
                    return redirect(url_for('getCart'))
        except Exception as e:
            print(e)
            return redirect(url_for('getCart'))


@app.route('/deleteitem/<string:id>')
def deleteitem(id):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('getCart'))
    try:
        if current_user.is_authenticated:
            current_user.cart = session['Shoppingcart']
            current_user.save()
        session.modified = True
        for key, item in session['Shoppingcart'].items():
            if str(key) == str(id):
                session['Shoppingcart'].pop(key, None)
                return redirect(url_for('getCart'))
    except Exception as e:
        print(e)
        return redirect(url_for('getCart'))


@app.route('/clearcart')
def clearcart():
    try:
        session.pop('Shoppingcart', None)
        if current_user.is_authenticated:
            current_user.cart = {}
            current_user.save()
        return redirect(url_for('getCart'))
    except Exception as e:
        print(e)
