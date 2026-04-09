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
app=Flask(__name__)
app.config.update(SECRET_KEY='x',SQLALCHEMY_DATABASE_URI='sqlite:///m.db',SQLALCHEMY_TRACK_MODIFICATIONS=False,REMEMBER_COOKIE_DURATION=timedelta(days=30))
db=SQLAlchemy(app)
lm=LoginManager(app)
lm.login_view='login'
C={'Tanzania':{'c':'TZ','tn':'TRA','tr':0.18,'cu':'TZS','l':'sw'},'Kenya':{'c':'KE','tn':'KRA','tr':0.16,'cu':'KES','l':'en'},'Nigeria':{'c':'NG','tn':'FIRS','tr':0.075,'cu':'NGN','l':'en'},'Rwanda':{'c':'RW','tn':'RRA','tr':0.18,'cu':'RWF','l':'en'},'Uganda':{'c':'UG','tn':'URA','tr':0.18,'cu':'UGX','l':'en'},'South Africa':{'c':'ZA','tn':'SARS','tr':0.15,'cu':'ZAR','l':'en'}}
class U(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    u=db.Column(db.String(80),unique=True)
    e=db.Column(db.String(120),unique=True)
    p=db.Column(db.String(20))
    co=db.Column(db.String(50),default='Tanzania')
    a=db.Column(db.Boolean,default=False)
    pw=db.Column(db.String(200))
    cr=db.Column(db.DateTime,default=datetime.utcnow)
    def set(self,pw): self.pw=generate_password_hash(pw)
    def chk(self,pw): return check_password_hash(self.pw,pw)
class S(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    oid=db.Column(db.Integer,db.ForeignKey('u.id'))
    n=db.Column(db.String(100))
    d=db.Column(db.Text)
    l=db.Column(db.String(200))
    ph=db.Column(db.String(20))
    i=db.Column(db.String(300))
    a=db.Column(db.Boolean,default=True)
    cr=db.Column(db.DateTime,default=datetime.utcnow)
class P(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sid=db.Column(db.Integer,db.ForeignKey('s.id'))
    n=db.Column(db.String(100))
    d=db.Column(db.Text)
    pr=db.Column(db.Float)
    c=db.Column(db.Float)
    q=db.Column(db.Float,default=0)
    th=db.Column(db.Float,default=5)
    u=db.Column(db.String(20),default='piece')
    ct=db.Column(db.String(50))
    i=db.Column(db.String(300))
    cr=db.Column(db.DateTime,default=datetime.utcnow)
class Sa(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sid=db.Column(db.Integer,db.ForeignKey('s.id'))
    pid=db.Column(db.Integer,db.ForeignKey('p.id'))
    q=db.Column(db.Float)
    sp=db.Column(db.Float)
    cp=db.Column(db.Float)
    tot=db.Column(db.Float)
    pf=db.Column(db.Float)
    cus=db.Column(db.String(100))
    pay=db.Column(db.String(50))
    cr=db.Column(db.DateTime,default=datetime.utcnow)
class H(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sid=db.Column(db.Integer,db.ForeignKey('s.id'))
    pid=db.Column(db.Integer,db.ForeignKey('p.id'))
    typ=db.Column(db.String(20))
    q=db.Column(db.Float)
    n=db.Column(db.String(200))
    cr=db.Column(db.DateTime,default=datetime.utcnow)
class Cm(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    uid=db.Column(db.Integer,db.ForeignKey('u.id'))
    r=db.Column(db.Integer)
    c=db.Column(db.Text)
    cr=db.Column(db.DateTime,default=datetime.utcnow)
    ap=db.Column(db.Boolean,default=True)
class A(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sid=db.Column(db.Integer,db.ForeignKey('s.id'))
    dt=db.Column(db.Date)
    typ=db.Column(db.String(20))
    sv=db.Column(db.Float)
    ex=db.Column(db.Float)
    ac=db.Column(db.Float)
    nt=db.Column(db.Text)
    cr=db.Column(db.DateTime,default=datetime.utcnow)
class Hm(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    uid=db.Column(db.Integer,db.ForeignKey('u.id'))
    sub=db.Column(db.String(200))
    msg=db.Column(db.Text)
    rep=db.Column(db.Text)
    st=db.Column(db.String(20),default='unread')
    cr=db.Column(db.DateTime,default=datetime.utcnow)
@lm.user_loader
def l(u): return U.query.get(int(u))
def ad(f):
    @wraps(f)
    def d(*a,**k):
        if not current_user.is_authenticated or not current_user.a:
            flash('Access denied','danger')
            return redirect(url_for('dashboard'))
        return f(*a,**k)
    return d
def cu(): return C[current_user.co]['cu'] if current_user.is_authenticated else 'TZS'
def lg(): return C[current_user.co]['l'] if current_user.is_authenticated else 'en'
@app.context_processor
def inj():
    if current_user.is_authenticated:
        c=C[current_user.co]
        return dict(lang=c['l'],tax_name=c['tn'],tax_rate=c['tr'],currency=c['cu'],COUNTRIES=C)
    return dict(lang='en',tax_name='TRA',tax_rate=0.18,currency='TZS',COUNTRIES=C)
def an(sid):
    e=date.today(); st=e-timedelta(30)
    sa=Sa.query.filter_by(sid=sid).filter(Sa.cr>=st).all()
    if len(sa)<7: return
    d={}
    for s in sa: d[s.cr.date()]=d.get(s.cr.date(),0)+s.tot
    a=[d.get(e-timedelta(i),0) for i in range(30)]
    m,std=np.mean(a),np.std(a)
    if std==0: return
    z=(d.get(e,0)-m)/std
    if abs(z)>1.5 and not A.query.filter_by(sid=sid,dt=e).first():
        db.session.add(A(sid=sid,dt=e,typ='spike' if d.get(e,0)>m else 'drop',sv=abs(z),ex=m,ac=d.get(e,0),nt=f"{'spike' if d.get(e,0)>m else 'drop'} detected"))
        db.session.commit()
def fc(sid):
    sa=Sa.query.filter_by(sid=sid).all()
    if len(sa)<7: return None,None
    d={}
    for s in sa: d[s.cr.strftime('%Y-%m-%d')]=d.get(s.cr.strftime('%Y-%m-%d'),0)+s.tot
    df=pd.DataFrame(list(d.items()),columns=['d','s'])
    df['d']=pd.to_datetime(df['d']); df=df.sort_values('d')
    df['n']=(df['d']-df['d'].min()).dt.days
    m=LinearRegression().fit(df[['n']].values,df['s'].values)
    return m,df['d'].max()
@app.route('/')
def i(): return render_template('index.html')
@app.route('/register',methods=['GET','POST'])
def r():
    if request.method=='POST':
        if request.form['p']!=request.form['c']: flash('Passwords mismatch','danger'); return redirect(url_for('r'))
        if U.query.filter_by(u=request.form['u']).first(): flash('Username taken','danger'); return redirect(url_for('r'))
        u=U(u=request.form['u'],e=request.form['e'],p=request.form['ph'],co=request.form['co'])
        u.set(request.form['p'])
        db.session.add(u); db.session.commit()
        flash('Registered! Please login.','success'); return redirect(url_for('l'))
    return render_template('register.html',countries=C.keys())
@app.route('/login',methods=['GET','POST'])
def l():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method=='POST':
        u=U.query.filter_by(u=request.form['u']).first()
        if u and u.chk(request.form['p']):
            login_user(u); flash(f'Welcome {u.u}!','success'); return redirect(url_for('dashboard'))
        flash('Invalid credentials','danger')
    return render_template('login.html')
@app.route('/logout')
@login_required
def lo(): logout_user(); flash('Logged out','info'); return redirect(url_for('i'))
@app.route('/set_country/<c>')
def sc(c):
    if current_user.is_authenticated: current_user.co=c; db.session.commit()
    else: session['country']=c
    return redirect(request.referrer or url_for('i'))
@app.route('/dashboard')
@login_required
def dashboard():
    ss=S.query.filter_by(oid=current_user.id).all()
    tp=sum(P.query.filter_by(sid=s.id).count() for s in ss)
    ts=sum(db.session.query(db.func.sum(Sa.tot)).filter(Sa.sid==s.id).scalar() or 0 for s in ss)
    return render_template('dashboard.html',shops=ss,total_products=tp,total_sales=ts)
@app.route('/shop/create',methods=['GET','POST'])
@login_required
def cs():
    if request.method=='POST':
        s=S(oid=current_user.id,n=request.form['n'],d=request.form.get('d',''),l=request.form.get('l',''),ph=request.form.get('ph',''),i=request.form.get('i',''))
        db.session.add(s); db.session.commit()
        flash('Shop created','success'); return redirect(url_for('ms',shop_id=s.id))
    return render_template('create_shop.html')
@app.route('/shop/<int:sid>')
@login_required
def ms(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id and not current_user.a: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    ps=P.query.filter_by(sid=s.id).all()
    rs=Sa.query.filter_by(sid=s.id).order_by(Sa.cr.desc()).limit(20).all()
    low=[p for p in ps if p.q<=p.th]
    ts=db.session.query(db.func.sum(Sa.tot)).filter(Sa.sid==s.id).scalar() or 0
    tp=db.session.query(db.func.sum(Sa.pf)).filter(Sa.sid==s.id).scalar() or 0
    return render_template('shop_dashboard.html',shop=s,products=ps,recent_sales=rs,low_stock_products=low,total_sales=ts,total_profit=tp)
@app.route('/shop/<int:sid>/product/add',methods=['GET','POST'])
@login_required
def ap(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    if request.method=='POST':
        p=P(sid=s.id,n=request.form['n'],d=request.form.get('d',''),pr=float(request.form['pr']),c=float(request.form['c']),q=float(request.form['q']),th=float(request.form.get('th',5)),u=request.form.get('u','piece'),ct=request.form.get('ct',''),i=request.form.get('i',''))
        db.session.add(p); db.session.commit(); flash('Product added','success')
        return redirect(url_for('ms',shop_id=s.id))
    return render_template('add_product.html',shop=s)
@app.route('/shop/<int:sid>/product/edit/<int:pid>',methods=['GET','POST'])
@login_required
def ep(sid,pid):
    s=S.query.get_or_404(sid); p=P.query.get_or_404(pid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    if request.method=='POST':
        p.n=request.form['n']; p.d=request.form.get('d',''); p.pr=float(request.form['pr']); p.c=float(request.form['c']); p.q=float(request.form['q']); p.th=float(request.form.get('th',5)); p.u=request.form.get('u','piece'); p.ct=request.form.get('ct',''); p.i=request.form.get('i','')
        db.session.commit(); flash('Product updated','success')
        return redirect(url_for('ms',shop_id=s.id))
    return render_template('edit_product.html',shop=s,product=p)
@app.route('/shop/<int:sid>/product/delete/<int:pid>')
@login_required
def dp(sid,pid):
    s=S.query.get_or_404(sid); p=P.query.get_or_404(pid)
    if s.oid!=current_user.id: flash('Access denied','danger')
    elif Sa.query.filter_by(pid=p.id).first(): flash('Cannot delete product with sales','danger')
    else: db.session.delete(p); db.session.commit(); flash('Product deleted','success')
    return redirect(url_for('ms',shop_id=s.id))
@app.route('/shop/<int:sid>/adjust_stock/<int:pid>',methods=['POST'])
@login_required
def as(sid,pid):
    s=S.query.get_or_404(sid); p=P.query.get_or_404(pid)
    if s.oid!=current_user.id: flash('Access denied','danger')
    else:
        q=float(request.form['q'])
        p.q+=q
        db.session.add(H(sid=s.id,pid=p.id,typ='add' if q>0 else 'remove',q=abs(q),n=request.form.get('n','')))
        db.session.commit(); flash(f'Stock adjusted by {q}','success')
    return redirect(url_for('ms',shop_id=s.id))
@app.route('/shop/<int:sid>/sell',methods=['GET','POST'])
@login_required
def sell(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    if request.method=='POST':
        p=P.query.get_or_404(request.form['pid'])
        if p.sid!=s.id: flash('Invalid product','danger')
        else:
            q=float(request.form['q'])
            if p.q<q: flash(f'Not enough stock. Only {p.q} {p.u}','danger')
            else:
                tot=p.pr*q; pf=(p.pr-p.c)*q
                sa=Sa(sid=s.id,pid=p.id,q=q,sp=p.pr,cp=p.c,tot=tot,pf=pf,cus=request.form.get('cus',''),pay=request.form.get('pay','Cash'))
                p.q-=q
                db.session.add(sa); db.session.commit(); an(s.id)
                flash(f'Sold {q} {p.u} of {p.n} for {cu()} {tot:,.0f}','success')
        return redirect(url_for('sell',shop_id=s.id))
    return render_template('sell.html',shop=s,products=P.query.filter_by(sid=s.id).filter(P.q>0).all())
