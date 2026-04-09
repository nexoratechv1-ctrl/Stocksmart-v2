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
@app.route('/shop/<int:sid>/sales_report')
@login_required
def sr(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id and not current_user.a: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    f=request.args.get('filter','today'); td=date.today()
    if f=='today': st=ed=td
    elif f=='week': st=td-timedelta(days=td.weekday()); ed=td
    elif f=='month': st=td.replace(day=1); ed=td
    else: st=datetime.strptime(request.args.get('start'),'%Y-%m-%d').date() if request.args.get('start') else td; ed=datetime.strptime(request.args.get('end'),'%Y-%m-%d').date() if request.args.get('end') else td
    sales=Sa.query.filter_by(sid=s.id).filter(db.func.date(Sa.cr)>=st, db.func.date(Sa.cr)<=ed).order_by(Sa.cr.desc()).all()
    ta=sum(x.tot for x in sales); tp=sum(x.pf for x in sales)
    return render_template('sales_report.html',shop=s,sales=sales,total_amount=ta,total_profit=tp,filter_type=f,start_date=st,end_date=ed)
@app.route('/shop/<int:sid>/low_stock')
@login_required
def ls(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    return render_template('low_stock.html',shop=s,low_stock_products=P.query.filter_by(sid=s.id).filter(P.q<=P.th).all())
@app.route('/shop/<int:sid>/tax_reminder')
@login_required
def tr(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    c=current_user.co; tr=C[c]['tr']; tn=C[c]['tn']
    ms=datetime(datetime.today().year,datetime.today().month,1)
    sales=Sa.query.filter_by(sid=s.id).filter(Sa.cr>=ms).all()
    ts=sum(x.tot for x in sales); vat=ts*tr
    td=datetime.today(); dd=datetime(td.year,td.month,20) if td.day<20 else datetime((td.replace(day=1)+timedelta(32)).year,(td.replace(day=1)+timedelta(32)).month,20)
    dl=(dd-td).days
    return render_template('tax_reminder.html',shop=s,tax_name=tn,tax_rate=tr,total_sales_this_month=ts,vat_due=vat,due_date=dd,days_left=dl)
@app.route('/shop/<int:sid>/ai_forecast')
@login_required
def af(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    m,ld=fc(s.id)
    if m is None: flash('Need 7 days of sales data','warning'); return redirect(url_for('ms',shop_id=s.id))
    last=(ld-datetime.now().date()).days+30
    preds=m.predict(np.array([[last+i] for i in range(1,8)]))
    preds=[max(0,round(p)) for p in preds]
    fc=[{'day':i+1,'sales':p} for i,p in enumerate(preds)]
    adv=[f"Avg daily: {cu()} {sum(preds)/7:,.0f}"]
    if preds[-1]>preds[0]*1.2: adv.append("⚠️ Sales increasing – order extra")
    elif preds[-1]<preds[0]*0.8: adv.append("ℹ️ Sales may decrease – avoid overstock")
    else: adv.append("✅ Sales stable")
    return render_template('ai_forecast.html',shop=s,forecast=fc,advice_list=adv)
@app.route('/shop/<int:sid>/anomaly_history')
@login_required
def ah(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    return render_template('anomaly_history.html',shop=s,anomalies=A.query.filter_by(sid=s.id).order_by(A.dt.desc()).all())
@app.route('/marketplace')
def mp():
    return render_template('marketplace.html',shops=S.query.filter_by(a=True).all())
@app.route('/search')
def se():
    q=request.args.get('q','').strip()
    if not q: return redirect(url_for('mp'))
    prods=P.query.join(S).filter((P.n.ilike(f'%{q}%'))|(P.d.ilike(f'%{q}%')),S.a==True).limit(50).all()
    return render_template('search_results.html',products=prods,query=q,currency=cu())
@app.route('/shop/view/<int:sid>')
def vs(sid):
    s=S.query.get_or_404(sid)
    return render_template('view_shop.html',shop=s,products=P.query.filter_by(sid=s.id).all(),currency=cu())
@app.route('/helpdesk',methods=['GET','POST'])
@login_required
def hd():
    if request.method=='POST':
        db.session.add(Hm(uid=current_user.id,sub=request.form['sub'],msg=request.form['msg']))
        db.session.commit(); flash('Message sent to admin','success'); return redirect(url_for('hd'))
    return render_template('helpdesk.html',messages=Hm.query.filter_by(uid=current_user.id).order_by(Hm.cr.desc()).all())
@app.route('/admin/help')
@login_required
@ad
def ahp():
    return render_template('admin_help.html',messages=Hm.query.order_by(Hm.cr.desc()).all())
@app.route('/admin/reply_message/<int:mid>',methods=['POST'])
@login_required
@ad
def arm(mid):
    h=Hm.query.get_or_404(mid)
    h.rep=request.form['rep']; h.st=request.form['st']
    db.session.commit(); flash('Reply sent','success'); return redirect(url_for('ahp'))
@app.route('/admin/delete_message/<int:mid>')
@login_required
@ad
def adm(mid):
    db.session.delete(Hm.query.get_or_404(mid)); db.session.commit(); flash('Deleted','success')
    return redirect(url_for('ahp'))
@app.route('/snake')
def sg(): return render_template('snake.html')
@app.route('/shop/<int:sid>/export_sales_pdf')
@login_required
def esp(sid):
    s=S.query.get_or_404(sid)
    if s.oid!=current_user.id and not current_user.a: flash('Access denied','danger'); return redirect(url_for('dashboard'))
    f=request.args.get('filter','today'); td=date.today()
    if f=='today': st=ed=td
    elif f=='week': st=td-timedelta(days=td.weekday()); ed=td
    elif f=='month': st=td.replace(day=1); ed=td
    else: st=datetime.strptime(request.args.get('start'),'%Y-%m-%d').date() if request.args.get('start') else td; ed=datetime.strptime(request.args.get('end'),'%Y-%m-%d').date() if request.args.get('end') else td
    sales=Sa.query.filter_by(sid=s.id).filter(db.func.date(Sa.cr)>=st, db.func.date(Sa.cr)<=ed).order_by(Sa.cr).all()
    ta=sum(x.tot for x in sales); tp=sum(x.pf for x in sales)
    html=render_template('sales_pdf.html',shop=s,sales=sales,total_amount=ta,total_profit=tp,start_date=st.strftime('%d/%m/%Y'),end_date=ed.strftime('%d/%m/%Y'),generation_date=datetime.now().strftime('%d/%m/%Y %H:%M'),currency=cu(),lang=lg())
    pdf=HTML(string=html).write_pdf()
    resp=app.make_response(pdf)
    resp.headers['Content-Type']='application/pdf'
    resp.headers['Content-Disposition']=f'attachment; filename=sales_report_{s.n}_{st}_{ed}.pdf'
    return resp
@app.route('/admin')
@login_required
@ad
def admd():
    return render_template('admin_dashboard.html',total_users=U.query.count(),total_shops=S.query.count(),total_sales_all=Sa.query.count(),total_revenue_all=db.session.query(db.func.sum(Sa.tot)).scalar() or 0,users=U.query.order_by(U.cr.desc()).all(),shops=S.query.order_by(S.cr.desc()).all(),help_messages=Hm.query.order_by(Hm.cr.desc()).limit(10).all())
@app.route('/admin/promote/<int:uid>')
@login_required
@ad
def apu(uid):
    u=U.query.get_or_404(uid)
    if u.id!=current_user.id: u.a=True; db.session.commit(); flash(f'{u.u} is now admin','success')
    else: flash('Cannot promote yourself','danger')
    return redirect(url_for('admd'))
@app.route('/admin/delete_user/<int:uid>')
@login_required
@ad
def adu(uid):
    u=U.query.get_or_404(uid)
    if u.id!=current_user.id: db.session.delete(u); db.session.commit(); flash('User deleted','success')
    else: flash('Cannot delete yourself','danger')
    return redirect(url_for('admd'))
@app.route('/admin/toggle_shop/<int:sid>')
@login_required
@ad
def ats(sid):
    s=S.query.get_or_404(sid)
    s.a=not s.a; db.session.commit()
    flash(f'Shop {s.n} {"activated" if s.a else "deactivated"}','success')
    return redirect(url_for('admd'))
@app.route('/admin/delete_shop/<int:sid>')
@login_required
@ad
def ads(sid):
    db.session.delete(S.query.get_or_404(sid)); db.session.commit(); flash('Shop deleted','success')
    return redirect(url_for('admd'))
@app.route('/profile',methods=['GET','POST'])
@login_required
def pr():
    if request.method=='POST':
        current_user.u=request.form['u']; current_user.e=request.form['e']; current_user.p=request.form['ph']; current_user.co=request.form['co']
        db.session.commit(); flash('Profile updated','success'); return redirect(url_for('pr'))
    return render_template('profile.html',user=current_user,countries=C.keys())
@app.route('/feedback',methods=['GET','POST'])
def fb():
    if request.method=='POST':
        if not current_user.is_authenticated: flash('Please login','warning'); return redirect(url_for('l'))
        r=int(request.form.get('rating',0)); c=request.form.get('comment','').strip()
        if r<1 or r>5 or not c: flash('Valid rating and comment required','danger')
        else: db.session.add(Cm(uid=current_user.id,r=r,c=c)); db.session.commit(); flash('Thank you!','success')
        return redirect(url_for('fb'))
    return render_template('feedback.html',comments=Cm.query.filter_by(ap=True).order_by(Cm.cr.desc()).all())
@app.route('/manifest.json')
def mf(): return app.send_static_file('manifest.json')
@app.route('/service-worker.js')
def sw(): return app.send_static_file('service-worker.js', mimetype='application/javascript')
def init():
    db.create_all()
    if not U.query.filter_by(u='admin').first():
        a=U(u='admin',e='admin@x.com',p='+255712345678',co='Tanzania',a=True)
        a.set('admin123')
        db.session.add(a); db.session.commit()
    if not S.query.first():
        db.session.add(S(oid=1,n='Demo Shop',d='Welcome to MultiStore',a=True))
        db.session.commit()
with app.app_context(): init()
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=True)
