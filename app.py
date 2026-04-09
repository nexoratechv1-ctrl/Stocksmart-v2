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
# ==================== HELPERS ====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def get_tax_rate(country):
    return COUNTRIES.get(country, {}).get('tax_rate', 0.18)

def get_currency(country):
    return COUNTRIES.get(country, {}).get('currency', 'TZS')

def get_language(country):
    return COUNTRIES.get(country, {}).get('language', 'en')

@app.context_processor
def inject_globals():
    lang = 'en'
    tax_name = 'TRA'
    tax_rate = 0.18
    currency = 'TZS'
    if current_user.is_authenticated:
        country = current_user.country
        lang = get_language(country)
        tax_name = COUNTRIES.get(country, {}).get('tax_name', 'TRA')
        tax_rate = COUNTRIES.get(country, {}).get('tax_rate', 0.18)
        currency = COUNTRIES.get(country, {}).get('currency', 'TZS')
    return dict(lang=lang, tax_name=tax_name, tax_rate=tax_rate, currency=currency, COUNTRIES=COUNTRIES)

# ==================== ANOMALY DETECTION ====================
def detect_anomalies(shop_id):
    end_date = date.today()
    start_date = end_date - timedelta(30)
    sales = Sale.query.filter_by(shop_id=shop_id).filter(Sale.created_at >= start_date).all()
    if len(sales) < 7:
        return
    daily = {}
    for s in sales:
        d = s.created_at.date()
        daily[d] = daily.get(d, 0) + s.total_amount
    arr = [daily.get(end_date - timedelta(i), 0) for i in range(30)]
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0:
        return
    today_sales = daily.get(end_date, 0)
    z = (today_sales - mean) / std
    if abs(z) > 1.5:
        typ = 'spike' if today_sales > mean else 'drop'
        existing = AnomalyLog.query.filter_by(shop_id=shop_id, date=end_date).first()
        if not existing:
            log = AnomalyLog(
                shop_id=shop_id,
                date=end_date,
                anomaly_type=typ,
                severity=abs(z),
                expected_sales=mean,
                actual_sales=today_sales,
                notes=f"{typ} detected. Expected ~{mean:.0f} got {today_sales:.0f}"
            )
            db.session.add(log)
            db.session.commit()

# ==================== AI FORECAST ====================
def train_sales_model(shop_id):
    sales = Sale.query.filter_by(shop_id=shop_id).all()
    if len(sales) < 7:
        return None, None
    data = {}
    for s in sales:
        d = s.created_at.strftime('%Y-%m-%d')
        data[d] = data.get(d, 0) + s.total_amount
    df = pd.DataFrame(list(data.items()), columns=['date', 'sales'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['day_num'] = (df['date'] - df['date'].min()).dt.days
    X = df[['day_num']].values
    y = df['sales'].values
    model = LinearRegression()
    model.fit(X, y)
    return model, df['date'].max()
