from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os
from flask_login import LoginManager
from flask_migrate import Migrate

from .config import Config
# from flask_login import LoginManager
# from shop.products.models import Register 
import pyrebase


# ---------- Firebase ----------
config = {
    "apiKey": "AIzaSyAbzMXHW-F63XzAJgqOIQxhfRJC_nP-iN0",
    "authDomain": "myshop-dc0d3.firebaseapp.com",
    "storageBucket": "myshop-dc0d3.appspot.com",
    "databaseURL": "https://myshop-dc0d3.firebaseapp.com/",
    "projectId": "myshop-dc0d3",
    "messagingSenderId": "1090563198053",
    "appId": "1:1090563198053:web:42f96da321a4d4a0d5ca8c",
    "measurementId": "G-D8R8PB4T3H"
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
# -------------------------------


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config.from_object(Config)
# ---------- Database ----------
# Chỉ dùng MySQL (myshop)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:gbao123@localhost:3306/myshop'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'something-secret'
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
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'customer_login'
login_manager.needs_refresh_message_category = 'danger'
login_manager.login_message = "Please login first"
# -------------------------------


# ---------- Import các Blueprint ----------
from shop.admin import routes
from shop.products import routes
from shop.carts import routes
from shop.customers import routes
# -------------------------------



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'customer_login'    # tên endpoint login của customer
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    # import "lười" (lazy import) để tránh vòng lặp
    from shop.products.models import Register    # hoặc đúng đường dẫn model user của bạn
    return Register.query.get(int(user_id))