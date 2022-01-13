import datetime
import hashlib

from flask import url_for, render_template, request, redirect, abort, send_from_directory, g, flash, session
from __init__ import app
import forms
from StorageRepo import *

gr = StorageRepo()
STR_LEN = 45


@app.route("/")
def index():
    return render_template('index.html', title="Главная",
                           counts=[])


@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get('loggedin'):
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = gr.login_user(form.login.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        if user:
            flash('Вы авторизовались!')
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))


@app.route("/suppliers")
def suppliers():
    return render_template('suppliers.html', title="Поставщики", ss=gr.get_suppliers())


@app.route("/suppliers/<int:supplierid>")
def supplier(supplierid):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('supplier.html', title="Поставщик", s=gr.get_supplier(supplierid),
                               ps=gr.get_products_of_supplier(supplierid))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('suppliers'))


@app.route("/suppliers/add", methods=['POST'])
def suppliers_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        n = request.form['name']
        a = request.form['address']
        p = request.form['phone']
        if 0 < len(n) < STR_LEN and 0 < len(a) < STR_LEN and 0 < len(p) < STR_LEN:
            gr.add_supplier(n, a, p)
        else:
            flash("Введите корректные данные")
    return redirect(url_for("suppliers"))


@app.route("/suppliers/rm/<int:id>")
def suppliers_rm(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.rm_supplier(id)
    return redirect(url_for("suppliers"))


@app.route("/products")
def products():
    return render_template('products.html', title="Товары", ss=gr.get_suppliers(), ps=gr.get_products(), us=gr.get_units())


@app.route("/products/<int:id>")
def product(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('product.html', title="Товар", p=gr.get_product(id), ss=gr.get_sales_of_product(id))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('products'))


@app.route("/products/add", methods=['POST'])
def products_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        p = request.form.get('id')
        n = request.form['name']
        u = request.form.get('uid')
        b = request.form['buy_price']
        s = request.form['sell_price']
        if p and 0 < len(n) < STR_LEN and u and 0 < len(b) < STR_LEN and 0 < len(s) < STR_LEN:
            b = int(b)
            s = int(s)
            if 0 < b < 10000 and 0 < s < 10000:
                gr.add_product(p, n, u, b, s)
            else:
                flash("Введите цену больше 0 или меньше 10000")
        else:
            flash("Введите корректные данные")
    return redirect(url_for("products"))


@app.route("/products/add_amount", methods=['POST'])
def products_add_amount():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        i = request.form.get('id')
        a = request.form['amount']
        if i and 0 < len(a) < STR_LEN:
            a = float(a)
            if 0 < a < 10000:
                gr.add_product_amount(int(i), a)
            else:
                flash("Введите число больше 0 или меньше 10000")
        else:
            flash("Заполните форму")
    return redirect(url_for("products"))


@app.route("/products/rm/<int:id>")
def products_remove(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.rm_product(id)
    return redirect(url_for("products"))


@app.route("/customers")
def customers():
    return render_template('customers.html', title="Покупатели", cs=gr.get_customers())


@app.route("/customers/add", methods=['POST'])
def customers_add():
    if session.get('role') == gr.ROLE_SUPERVISOR:
        n = request.form['name']
        a = request.form['address']
        p = request.form['phone']
        if 0 < len(n) < STR_LEN and 0 < len(a) < STR_LEN and 0 < len(p) < STR_LEN:
            gr.add_customer(n, a, p)
        else:
            flash("Заполните форму")
    return redirect(url_for("customers"))


@app.route("/customers/<int:id>")
def customer(id):
    c = gr.get_customer(id)
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('customer.html', title="Покупатель", c=c, ss=gr.get_sales_of_customer(id))
    else:
        flash("Недостаточно прав")
        return redirect(url_for('customers'))


@app.route("/customers/rm/<int:id>")
def customers_remove(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.rm_customer(id)
    return redirect(url_for("customers"))


@app.route("/sales")
def sales():
    return render_template('sales.html', title="Продажи", sales=gr.get_sales(), cs=gr.get_customers(), ps=gr.get_products())


@app.route("/sales/<int:id>")
def sale(id):
    s = gr.get_sale(id)
    if session.get('role') == gr.ROLE_SUPERVISOR:
        return render_template('sale.html', title="Продажа", s=s)
    else:
        flash("Недостаточно прав")
        return redirect(url_for('sales'))


@app.route("/sales/add", methods=['POST'])
def sales_add():
    if session.get('role') >= gr.ROLE_SELLER:
        dt = request.form['datetime']
        c = request.form.get('cid')
        p = request.form.get('pid')
        a = request.form['amount']
        if dt and c and p and 0 < len(a) < STR_LEN:
            a = float(a)
            if a > 0:
                if not gr.add_sale(d=dt, c=int(c), p=int(p), a=a):
                    flash("Не хватает товара")
            else:
                flash("Введите количество больше 0")
        else:
            flash("Введите корректные данные")
    return redirect(url_for("sales"))


@app.route("/sales/rm/<int:id>")
def sales_remove(id):
    if session.get('role') == gr.ROLE_SUPERVISOR:
        if id:
            gr.remove_sale(id)
    return redirect(url_for("sales"))


@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
@app.route('/style.css')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
