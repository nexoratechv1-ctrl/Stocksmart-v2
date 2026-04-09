import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import json
from weasyprint import HTML

app = Flask(__name__)
app.config['SECRET_KEY'] = 'multistore-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///multistore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== COUNTRIES & TAX RATES ====================
COUNTRIES = {
    'Tanzania': {'code': 'TZ', 'tax_name': 'TRA', 'tax_rate': 0.18, 'currency': 'TZS', 'language': 'sw'},
    'Kenya': {'code': 'KE', 'tax_name': 'KRA', 'tax_rate': 0.16, 'currency': 'KES', 'language': 'en'},
    'Nigeria': {'code': 'NG', 'tax_name': 'FIRS', 'tax_rate': 0.075, 'currency': 'NGN', 'language': 'en'},
    'Rwanda': {'code': 'RW', 'tax_name': 'RRA', 'tax_rate': 0.18, 'currency': 'RWF', 'language': 'en'},
    'Uganda': {'code': 'UG', 'tax_name': 'URA', 'tax_rate': 0.18, 'currency': 'UGX', 'language': 'en'},
    'South Africa': {'code': 'ZA', 'tax_name': 'SARS', 'tax_rate': 0.15, 'currency': 'ZAR', 'language': 'en'}
}
# ==================== MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(50), default='Tanzania')
    is_admin = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    image_url = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.relationship('User', backref=db.backref('shops', lazy=True))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, default=0)
    low_stock_threshold = db.Column(db.Float, default=5)
    unit = db.Column(db.String(20), default='piece')
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shop = db.relationship('Shop', backref=db.backref('products', lazy=True))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    customer_name = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref=db.backref('sales', lazy=True))

class StockHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    change_type = db.Column(db.String(20))
    quantity = db.Column(db.Float)
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True)

class AnomalyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    date = db.Column(db.Date, nullable=False)
    anomaly_type = db.Column(db.String(20))
    severity = db.Column(db.Float)
    expected_sales = db.Column(db.Float)
    actual_sales = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HelpMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='unread')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('help_messages', lazy=True))
