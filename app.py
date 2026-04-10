import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from weasyprint import HTML

# ------------------- APP CONFIG -------------------
app = Flask(__name__)
app.config.update(
    SECRET_KEY='multistore-secret-key',
    SQLALCHEMY_DATABASE_URI='sqlite:///multistore.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    REMEMBER_COOKIE_DURATION=timedelta(days=30)
)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ------------------- COUNTRIES DATA -------------------
COUNTRIES = {
    'Tanzania': {'code': 'TZ', 'tax_name': 'TRA', 'tax_rate': 0.18, 'currency': 'TZS', 'lang': 'sw'},
    'Kenya': {'code': 'KE', 'tax_name': 'KRA', 'tax_rate': 0.16, 'currency': 'KES', 'lang': 'en'},
    'Nigeria': {'code': 'NG', 'tax_name': 'FIRS', 'tax_rate': 0.075, 'currency': 'NGN', 'lang': 'en'},
    'Rwanda': {'code': 'RW', 'tax_name': 'RRA', 'tax_rate': 0.18, 'currency': 'RWF', 'lang': 'en'},
    'Uganda': {'code': 'UG', 'tax_name': 'URA', 'tax_rate': 0.18, 'currency': 'UGX', 'lang': 'en'},
    'South Africa': {'code': 'ZA', 'tax_name': 'SARS', 'tax_rate': 0.15, 'currency': 'ZAR', 'lang': 'en'}
}

# ------------------- MODELS -------------------
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
    response = db.Column(db.Text)
    status = db.Column(db.String(20), default='unread')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('help_messages', lazy=True))

# ------------------- HELPER FUNCTIONS -------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_currency(country):
    return COUNTRIES.get(country, {}).get('currency', 'TZS')

def get_language(country):
    return COUNTRIES.get(country, {}).get('lang', 'en')

def get_tax_rate(country):
    return COUNTRIES.get(country, {}).get('tax_rate', 0.18)

@app.context_processor
def inject_globals():
    if current_user.is_authenticated:
        c = COUNTRIES[current_user.country]
        return dict(
            lang=c['lang'],
            tax_name=c['tax_name'],
            tax_rate=c['tax_rate'],
            currency=c['currency'],
            COUNTRIES=COUNTRIES
        )
    return dict(lang='en', tax_name='TRA', tax_rate=0.18, currency='TZS', COUNTRIES=COUNTRIES)

# ------------------- ANOMALY DETECTION -------------------
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
    if abs(z) > 1.5 and not AnomalyLog.query.filter_by(shop_id=shop_id, date=end_date).first():
        typ = 'spike' if today_sales > mean else 'drop'
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

# ------------------- AI SALES FORECAST -------------------
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
    # ------------------- PUBLIC ROUTES -------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        country = request.form['country']
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email, phone=phone, country=country)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', countries=COUNTRIES.keys())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/set_country/<country>')
def set_country(country):
    if current_user.is_authenticated:
        current_user.country = country
        db.session.commit()
    else:
        session['country'] = country
    return redirect(request.referrer or url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    shops = Shop.query.filter_by(owner_id=current_user.id).all()
    total_products = sum(Product.query.filter_by(shop_id=shop.id).count() for shop in shops)
    total_sales = sum(db.session.query(db.func.sum(Sale.total_amount)).filter(Sale.shop_id==shop.id).scalar() or 0 for shop in shops)
    return render_template('dashboard.html', shops=shops, total_products=total_products, total_sales=total_sales)

# ------------------- SHOP MANAGEMENT -------------------
@app.route('/shop/create', methods=['GET', 'POST'])
@login_required
def create_shop():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        location = request.form.get('location', '')
        phone = request.form.get('phone', '')
        image_url = request.form.get('image_url', '')
        shop = Shop(owner_id=current_user.id, name=name, description=description,
                    location=location, phone=phone, image_url=image_url)
        db.session.add(shop)
        db.session.commit()
        flash('Shop created successfully!', 'success')
        return redirect(url_for('manage_shop', shop_id=shop.id))
    return render_template('create_shop.html')

@app.route('/shop/<int:shop_id>')
@login_required
def manage_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    products = Product.query.filter_by(shop_id=shop.id).all()
    recent_sales = Sale.query.filter_by(shop_id=shop.id).order_by(Sale.created_at.desc()).limit(20).all()
    low_stock_products = [p for p in products if p.quantity <= p.low_stock_threshold]
    total_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(Sale.shop_id==shop.id).scalar() or 0
    total_profit = db.session.query(db.func.sum(Sale.profit)).filter(Sale.shop_id==shop.id).scalar() or 0
    return render_template('shop_dashboard.html',
                           shop=shop, products=products, recent_sales=recent_sales,
                           low_stock_products=low_stock_products,
                           total_sales=total_sales, total_profit=total_profit)
@app.route('/shop/<int:shop_id>/product/add', methods=['GET', 'POST'])
@login_required
def add_product(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        price = float(request.form['price'])
        cost_price = float(request.form['cost_price'])
        quantity = float(request.form['quantity'])
        low_stock_threshold = float(request.form.get('low_stock_threshold', 5))
        unit = request.form.get('unit', 'piece')
        category = request.form.get('category', '')
        image_url = request.form.get('image_url', '')
        product = Product(shop_id=shop.id, name=name, description=description,
                          price=price, cost_price=cost_price, quantity=quantity,
                          low_stock_threshold=low_stock_threshold, unit=unit,
                          category=category, image_url=image_url)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully', 'success')
        return redirect(url_for('manage_shop', shop_id=shop.id))
    return render_template('add_product.html', shop=shop)

@app.route('/shop/<int:shop_id>/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(shop_id, product_id):
    shop = Shop.query.get_or_404(shop_id)
    product = Product.query.get_or_404(product_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form.get('description', '')
        product.price = float(request.form['price'])
        product.cost_price = float(request.form['cost_price'])
        product.quantity = float(request.form['quantity'])
        product.low_stock_threshold = float(request.form.get('low_stock_threshold', 5))
        product.unit = request.form.get('unit', 'piece')
        product.category = request.form.get('category', '')
        product.image_url = request.form.get('image_url', '')
        db.session.commit()
        flash('Product updated', 'success')
        return redirect(url_for('manage_shop', shop_id=shop.id))
    return render_template('edit_product.html', shop=shop, product=product)

@app.route('/shop/<int:shop_id>/product/delete/<int:product_id>')
@login_required
def delete_product(shop_id, product_id):
    shop = Shop.query.get_or_404(shop_id)
    product = Product.query.get_or_404(product_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if Sale.query.filter_by(product_id=product.id).first():
        flash('Cannot delete product with sales history', 'danger')
    else:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted', 'success')
    return redirect(url_for('manage_shop', shop_id=shop.id))

@app.route('/shop/<int:shop_id>/adjust_stock/<int:product_id>', methods=['POST'])
@login_required
def adjust_stock(shop_id, product_id):
    shop = Shop.query.get_or_404(shop_id)
    product = Product.query.get_or_404(product_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    qty = float(request.form['quantity'])
    note = request.form.get('note', '')
    product.quantity += qty
    hist = StockHistory(shop_id=shop.id, product_id=product.id,
                        change_type='add' if qty > 0 else 'remove',
                        quantity=abs(qty), note=note)
    db.session.add(hist)
    db.session.commit()
    flash(f'Stock adjusted by {qty}', 'success')
    return redirect(url_for('manage_shop', shop_id=shop.id))
@app.route('/shop/<int:shop_id>/sell', methods=['GET', 'POST'])
@login_required
def sell(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = float(request.form['quantity'])
        product = Product.query.get_or_404(product_id)
        if product.shop_id != shop.id:
            flash('Invalid product', 'danger')
            return redirect(url_for('sell', shop_id=shop.id))
        if product.quantity < quantity:
            flash(f'Not enough stock. Only {product.quantity} {product.unit} available', 'danger')
            return redirect(url_for('sell', shop_id=shop.id))
        total = product.price * quantity
        profit = (product.price - product.cost_price) * quantity
        sale = Sale(shop_id=shop.id, product_id=product.id, quantity=quantity,
                    selling_price=product.price, cost_price=product.cost_price,
                    total_amount=total, profit=profit,
                    customer_name=request.form.get('customer_name', ''),
                    payment_method=request.form.get('payment_method', 'Cash'))
        product.quantity -= quantity
        db.session.add(sale)
        db.session.commit()
        detect_anomalies(shop.id)
        flash(f'Sold {quantity} {product.unit} of {product.name} for {get_currency(current_user.country)} {total:,.0f}', 'success')
        return redirect(url_for('sell', shop_id=shop.id))
    products = Product.query.filter_by(shop_id=shop.id).filter(Product.quantity > 0).all()
    return render_template('sell.html', shop=shop, products=products)

@app.route('/shop/<int:shop_id>/sales_report')
@login_required
def sales_report(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    filter_type = request.args.get('filter', 'today')
    today = date.today()
    if filter_type == 'today':
        start = end = today
    elif filter_type == 'week':
        start = today - timedelta(days=today.weekday())
        end = today
    elif filter_type == 'month':
        start = today.replace(day=1)
        end = today
    elif filter_type == 'custom':
        start = datetime.strptime(request.args.get('start'), '%Y-%m-%d').date() if request.args.get('start') else today
        end = datetime.strptime(request.args.get('end'), '%Y-%m-%d').date() if request.args.get('end') else today
    else:
        start = end = today
    sales = Sale.query.filter_by(shop_id=shop.id).filter(
        db.func.date(Sale.created_at) >= start,
        db.func.date(Sale.created_at) <= end
    ).order_by(Sale.created_at.desc()).all()
    total_amount = sum(s.total_amount for s in sales)
    total_profit = sum(s.profit for s in sales)
    return render_template('sales_report.html',
                           shop=shop, sales=sales,
                           total_amount=total_amount, total_profit=total_profit,
                           filter_type=filter_type, start_date=start, end_date=end)

@app.route('/shop/<int:shop_id>/low_stock')
@login_required
def low_stock(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    products = Product.query.filter_by(shop_id=shop.id).filter(Product.quantity <= Product.low_stock_threshold).all()
    return render_template('low_stock.html', shop=shop, low_stock_products=products)
@app.route('/shop/<int:shop_id>/tax_reminder')
@login_required
def tax_reminder(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    country = current_user.country
    tax_rate = get_tax_rate(country)
    tax_name = COUNTRIES[country]['tax_name']
    month_start = datetime(datetime.today().year, datetime.today().month, 1)
    sales_this_month = Sale.query.filter_by(shop_id=shop.id).filter(Sale.created_at >= month_start).all()
    total_sales = sum(s.total_amount for s in sales_this_month)
    vat_due = total_sales * tax_rate
    td = datetime.today()
    if td.day < 20:
        due_date = datetime(td.year, td.month, 20)
    else:
        next_month = td.replace(day=1) + timedelta(days=32)
        due_date = datetime(next_month.year, next_month.month, 20)
    days_left = (due_date - td).days
    return render_template('tax_reminder.html',
                           shop=shop, tax_name=tax_name, tax_rate=tax_rate,
                           total_sales_this_month=total_sales, vat_due=vat_due,
                           due_date=due_date, days_left=days_left)

@app.route('/shop/<int:shop_id>/ai_forecast')
@login_required
def ai_forecast(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    model, last_date = train_sales_model(shop.id)
    if model is None:
        flash('Not enough sales data (need at least 7 days).', 'warning')
        return redirect(url_for('manage_shop', shop_id=shop.id))
    last_day = (last_date - datetime.now().date()).days + 30
    future_days = np.array([[last_day + i] for i in range(1, 8)])
    predictions = model.predict(future_days)
    predictions = [max(0, round(p)) for p in predictions]
    forecast = [{'day': i+1, 'sales': p} for i, p in enumerate(predictions)]
    advice_list = [f"Predicted average daily sales next week: {get_currency(current_user.country)} {sum(predictions)/7:,.0f}"]
    if predictions[-1] > predictions[0] * 1.2:
        advice_list.append("⚠️ Sales are increasing! Order extra stock for next week.")
    elif predictions[-1] < predictions[0] * 0.8:
        advice_list.append("ℹ️ Sales may decrease. Avoid overstocking.")
    else:
        advice_list.append("✅ Sales are stable. Maintain current stock levels.")
    return render_template('ai_forecast.html', shop=shop, forecast=forecast, advice_list=advice_list)

@app.route('/shop/<int:shop_id>/anomaly_history')
@login_required
def anomaly_history(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    anomalies = AnomalyLog.query.filter_by(shop_id=shop.id).order_by(AnomalyLog.date.desc()).all()
    return render_template('anomaly_history.html', shop=shop, anomalies=anomalies)

# ------------------- MARKETPLACE & SEARCH -------------------
@app.route('/marketplace')
def marketplace():
    shops = Shop.query.filter_by(is_active=True).all()
    return render_template('marketplace.html', shops=shops)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('marketplace'))
    products = Product.query.join(Shop).filter(
        (Product.name.ilike(f'%{query}%')) | (Product.description.ilike(f'%{query}%')),
        Shop.is_active == True
    ).limit(50).all()
    currency = get_currency(current_user.country) if current_user.is_authenticated else 'TZS'
    return render_template('search_results.html', products=products, query=query, currency=currency)

@app.route('/shop/view/<int:shop_id>')
def view_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    products = Product.query.filter_by(shop_id=shop.id).all()
    currency = get_currency(current_user.country) if current_user.is_authenticated else 'TZS'
    return render_template('view_shop.html', shop=shop, products=products, currency=currency) 
# ------------------- HELPDESK -------------------
@app.route('/helpdesk', methods=['GET', 'POST'])
@login_required
def helpdesk():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        help_msg = HelpMessage(user_id=current_user.id, subject=subject, message=message)
        db.session.add(help_msg)
        db.session.commit()
        flash('Message sent to admin. You will be contacted soon.', 'success')
        return redirect(url_for('helpdesk'))
    messages = HelpMessage.query.filter_by(user_id=current_user.id).order_by(HelpMessage.created_at.desc()).all()
    return render_template('helpdesk.html', messages=messages)

@app.route('/admin/help')
@login_required
@admin_required
def admin_help():
    messages = HelpMessage.query.order_by(HelpMessage.created_at.desc()).all()
    return render_template('admin_help.html', messages=messages)

@app.route('/admin/reply_message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def admin_reply_message(message_id):
    msg = HelpMessage.query.get_or_404(message_id)
    msg.response = request.form.get('response')
    msg.status = request.form.get('status')
    db.session.commit()
    flash('Reply sent and status updated.', 'success')
    return redirect(url_for('admin_help'))

@app.route('/admin/delete_message/<int:message_id>')
@login_required
@admin_required
def admin_delete_message(message_id):
    msg = HelpMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_help'))

# ------------------- SNAKE GAME -------------------
@app.route('/snake')
def snake_game():
    return render_template('snake.html')

# ------------------- PDF EXPORT -------------------
@app.route('/shop/<int:shop_id>/export_sales_pdf')
@login_required
def export_sales_pdf(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if shop.owner_id != current_user.id and not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    filter_type = request.args.get('filter', 'today')
    today = date.today()
    if filter_type == 'today':
        start = end = today
    elif filter_type == 'week':
        start = today - timedelta(days=today.weekday())
        end = today
    elif filter_type == 'month':
        start = today.replace(day=1)
        end = today
    elif filter_type == 'custom':
        start = datetime.strptime(request.args.get('start'), '%Y-%m-%d').date() if request.args.get('start') else today
        end = datetime.strptime(request.args.get('end'), '%Y-%m-%d').date() if request.args.get('end') else today
    else:
        start = end = today
    sales = Sale.query.filter_by(shop_id=shop.id).filter(
        db.func.date(Sale.created_at) >= start,
        db.func.date(Sale.created_at) <= end
    ).order_by(Sale.created_at).all()
    total_amount = sum(s.total_amount for s in sales)
    total_profit = sum(s.profit for s in sales)
    html_content = render_template('sales_pdf.html',
                                   shop=shop, sales=sales,
                                   total_amount=total_amount, total_profit=total_profit,
                                   start_date=start.strftime('%d/%m/%Y'),
                                   end_date=end.strftime('%d/%m/%Y'),
                                   generation_date=datetime.now().strftime('%d/%m/%Y %H:%M'),
                                   currency=get_currency(current_user.country),
                                   lang=get_language(current_user.country))
    pdf = HTML(string=html_content).write_pdf()
    response = app.make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=sales_report_{shop.name}_{start}_{end}.pdf'
    return response
# ------------------- ADMIN DASHBOARD -------------------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_shops = Shop.query.count()
    total_sales_all = Sale.query.count()
    total_revenue_all = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
    users = User.query.order_by(User.created_at.desc()).all()
    shops = Shop.query.order_by(Shop.created_at.desc()).all()
    help_messages = HelpMessage.query.order_by(HelpMessage.created_at.desc()).limit(10).all()
    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_shops=total_shops,
                           total_sales_all=total_sales_all,
                           total_revenue_all=total_revenue_all,
                           users=users,
                           shops=shops,
                           help_messages=help_messages)

@app.route('/admin/promote/<int:user_id>')
@login_required
@admin_required
def admin_promote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot promote yourself.', 'danger')
    else:
        user.is_admin = True
        db.session.commit()
        flash(f'User {user.username} is now an admin.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_shop/<int:shop_id>')
@login_required
@admin_required
def admin_toggle_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop.is_active = not shop.is_active
    db.session.commit()
    status = 'activated' if shop.is_active else 'deactivated'
    flash(f'Shop {shop.name} has been {status}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_shop/<int:shop_id>')
@login_required
@admin_required
def admin_delete_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    db.session.delete(shop)
    db.session.commit()
    flash('Shop deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ------------------- PROFILE & FEEDBACK -------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.phone = request.form['phone']
        current_user.country = request.form['country']
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user, countries=COUNTRIES.keys())

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please login to leave feedback.', 'warning')
            return redirect(url_for('login'))
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        if rating < 1 or rating > 5 or not comment:
            flash('Please provide a valid rating (1-5) and comment.', 'danger')
            return redirect(url_for('feedback'))
        new_comment = Comment(user_id=current_user.id, rating=rating, comment=comment)
        db.session.add(new_comment)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback'))
    comments = Comment.query.filter_by(is_approved=True).order_by(Comment.created_at.desc()).all()
    return render_template('feedback.html', comments=comments)
# ------------------- PWA (Progressive Web App) -------------------
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js', mimetype='application/javascript')

# ------------------- INITIALIZATION -------------------
def init_db():
    db.create_all()
    # Create admin user if none exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@multistore.com', phone='+255712345678',
                     country='Tanzania', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username 'admin', password 'admin123'")
    # Create a demo shop if no shops exist
    if not Shop.query.first():
        demo_shop = Shop(owner_id=1, name='Demo Shop', description='Welcome to MultiStore', is_active=True)
        db.session.add(demo_shop)
        db.session.commit()
        print("Demo shop created.")

# ------------------- RUN APP -------------------
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
                           
                           
