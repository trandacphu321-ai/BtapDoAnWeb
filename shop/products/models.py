from shop import db
from datetime import datetime
from shop.customers.models import Register
from flask_login import UserMixin


class Addproduct(db.Document):
    name = db.StringField(max_length=80, required=True)
    price = db.FloatField(required=True)
    discount = db.IntField(default=0)
    stock = db.IntField(required=True)
    colors = db.StringField(required=True)
    capacity = db.StringField(default="") 
    desc = db.StringField(required=True)
    pub_date = db.DateTimeField(default=datetime.utcnow)

    category = db.ReferenceField('Category', required=True)
    brand = db.ReferenceField('Brand', required=True)

    image_1 = db.StringField(required=True, default='image1.jpg')
    image_2 = db.StringField(required=True, default='image2.jpg')
    image_3 = db.StringField(required=True, default='image3.jpg')
    image_4 = db.StringField(required=False, default='image4.jpg')
    image_5 = db.StringField(required=False, default='image5.jpg')
    video_link = db.StringField(required=False, default='')
    review_video = db.StringField(required=False, default='')

    meta = {
        'collection': 'products', 
        'strict': False,
        'indexes': ['name', 'category', 'brand', 'price']
    }

    def __repr__(self):
        return '<Addproduct %r>' % self.name


class Category(db.Document):
    name = db.StringField(max_length=30, required=True, unique=True)

    meta = {'collection': 'categories'}

    def __repr__(self):
        return '<Category %r>' % self.name


class Brand(db.Document):
    category = db.ReferenceField('Category')
    name = db.StringField(max_length=30, required=True)

    meta = {'collection': 'brands'}

    def __repr__(self):
        return '<Brand %r>' % self.name


class Rate(db.Document):
    product = db.ReferenceField('Addproduct', required=True)
    user_id = db.StringField(required=True) # Changed from register to avoid circular import immediately

    time = db.DateTimeField(default=datetime.utcnow)
    desc = db.StringField(required=True)
    rate_number = db.IntField(required=True)
    performance_rate = db.IntField(default=5)
    battery_rate = db.IntField(default=5)
    camera_rate = db.IntField(default=5)

    meta = {'collection': 'rates'}

    def __repr__(self):
        return '<Rate %r>' % self.id

class UserInteraction(db.Document):
    user_id = db.StringField(required=True)
    product_id = db.StringField(required=True)
    interaction_type = db.StringField(required=True, choices=('view', 'cart', 'purchase'))
    weight = db.IntField(required=True, default=1)
    timestamp = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_interactions',
        'indexes': ['user_id', 'product_id', 'interaction_type']
    }

    def __repr__(self):
        return '<UserInteraction %r %r>' % (self.user_id, self.product_id)

class Coupon(db.Document):
    code = db.StringField(max_length=50, required=True, unique=True)
    discount_type = db.StringField(choices=('fixed', 'percent'), default='fixed')
    discount_value = db.FloatField(required=True)
    expiry_date = db.DateTimeField(required=True)
    usage_limit = db.IntField(default=100)
    used_count = db.IntField(default=0)
    is_active = db.BooleanField(default=True)

    meta = {'collection': 'coupons'}

    def __repr__(self):
        return '<Coupon %r>' % self.code
