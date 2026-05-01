from flask import Flask, render_template
from flask_mongoengine import MongoEngine
from flask_bcrypt import Bcrypt
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os
from flask_login import LoginManager
from flask_caching import Cache

from .config import Config
# from flask_login import LoginManager
# from shop.products.models import Register 
import pyrebase
from dotenv import load_dotenv

load_dotenv()

# ---------- Firebase ----------
config = {
    "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyCE0YWF...6iSUUXM"), # Thay thế phần bị che nếu cần
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "myshop-dc0d3-835b2.firebaseapp.com"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "myshop-dc0d3-835b2.firebasestorage.app"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "https://myshop-dc0d3-835b2.firebaseio.com"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "myshop-dc0d3-835b2"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "330579814492"),
    "appId": os.getenv("FIREBASE_APP_ID", "1:330579814492:web:2010c7e5f320a5db061e99"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "G-DT7F0TNXCE")
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
# -------------------------------


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config.from_object(Config)
# ---------- Database ----------
app.config['MONGODB_SETTINGS'] = {
    'host': os.getenv("MONGODB_URI"),
    'tls': True,
    'tlsAllowInvalidCertificates': True
}
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret-key")

# ---------- Caching ----------
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)
# -------------------------------

# ---------- Upload Settings ----------
# Nếu folder ảnh nằm ở project_root/static/images
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, '..', 'static', 'images')
# Giới hạn dung lượng upload tối đa 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
# -------------------------------


# ---------- Flask Extensions ----------
db = MongoEngine(app)
bcrypt = Bcrypt(app)

@app.template_filter('vnd')
def vnd_format(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value).replace(',', '.') + 'đ'
    except (ValueError, TypeError):
        return value

@app.template_filter('firebase_image')
def firebase_image(filename):
    if not filename:
        return ""
    if str(filename).startswith("http"):
        return filename
    bucket = app.config.get("FIREBASE_STORAGE_BUCKET") or os.getenv("FIREBASE_STORAGE_BUCKET", "myshop-dc0d3-835b2.firebasestorage.app")
    return f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/images%2F{filename}?alt=media"


login_manager = LoginManager(app)
login_manager.login_view = 'customer_login'
login_manager.needs_refresh_message_category = 'danger'
login_manager.login_message = "Please login first"
# -------------------------------

@app.context_processor
def inject_pending_orders():
    try:
        from shop.customers.models import CustomerOrder
        count = CustomerOrder.objects(status='Pending').count()
        return dict(pending_orders_count=count)
    except:
        return dict(pending_orders_count=0)


# ---------- Import các Blueprint ----------
from shop.admin import routes
from shop.products import routes
from shop.carts import routes
from shop.customers import routes
from shop.api import routes as api_routes    # Giai đoạn 5: REST API
from shop import chatbot
# -------------------------------

# ---------- Error Handlers ----------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500
# -------------------------------