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
