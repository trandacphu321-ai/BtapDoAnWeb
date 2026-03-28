# shop/config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'your-secret-key'           # nhớ đổi
    SQLALCHEMY_DATABASE_URI = 'sqlite:///shop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
