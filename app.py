from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
import timeit
import datetime
import os
from wtforms.fields.html5 import EmailField
from firebase import firebase
IIDD=1


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/image/product'

# Config MySQL
mysql = MySQL()
app.config['MYSQL_HOST'] = 'mysql-j0h5nn.alwaysdata.net'
app.config['MYSQL_USER'] = 'j0h5nn'
app.config['MYSQL_PASSWORD'] = 'x3y4zK76RM1Lf2$38ktQ'
app.config['MYSQL_DB'] = 'j0h5nn_saludables'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Initialize the app for use with this MySQL class
mysql.init_app(app)
#Inicializar firebase
firebase = firebase.FirebaseApplication("https://antojossaludable1234.firebaseio.com/",None)
import mysql.connector as mc

mydb = mc.connect(
  host="mysql-j0h5nn.alwaysdata.net",
  user="j0h5nn",
  password="x3y4zK76RM1Lf2$38ktQ",
  database="j0h5nn_saludables"
)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return redirect(url_for('index'))
        else:
            return f(*args, *kwargs)

    return wrap


def is_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('admin_login'))

    return wrap


def not_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return redirect(url_for('admin'))
        else:
            return f(*args, *kwargs)

    return wrap


def wrappers(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)

    return wrapped


def content_based_filtering(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))  # getting id row
    data = cur.fetchone()  # get row info
    data_cat = data['category']  # get id category ex shirt
    print('Showing result for Product Id: ' + product_id)
    category_matched = cur.execute("SELECT * FROM products WHERE category=%s", (data_cat,))  # get all shirt category
    print('Total product matched: ' + str(category_matched))
    cat_product = cur.fetchall()  # get all row
    cur.execute("SELECT * FROM product_level WHERE product_id=%s", (product_id,))  # id level info
    id_level = cur.fetchone()
    recommend_id = []
    cate_level = ['v_shape', 'polo', 'clean_text', 'design', 'leather', 'color', 'formal', 'converse', 'loafer', 'hook',
                  'chain']
    for product_f in cat_product:
        cur.execute("SELECT * FROM product_level WHERE product_id=%s", (product_f['id'],))
        f_level = cur.fetchone()
        match_score = 0
        try:
            if f_level['product_id'] != int(product_id):
                for cat_level in cate_level:
                    if f_level[cat_level] == id_level[cat_level]:
                        match_score += 1
                if match_score == 11:
                    recommend_id.append(f_level['product_id'])
        except:
            recommend_id.append(11)
    print('Total recommendation found: ' + str(recommend_id))
    if recommend_id:
        cur = mysql.connection.cursor()
        placeholders = ','.join((str(n) for n in recommend_id))
        query = 'SELECT * FROM products WHERE id IN (%s)' % placeholders
        cur.execute(query)
        recommend_list = cur.fetchall()
        return recommend_list, recommend_id, category_matched, product_id
    else:
        return ''


@app.route('/')
def index():
    form = OrderForm(request.form)
    # Create cursor
    cur = mysql.connection.cursor()
    # Get message
    values = 'tortas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY RAND() LIMIT 4", (values,))
    tortas = cur.fetchall()
    values = 'Anchetas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY RAND() LIMIT 4", (values,))
    Anchetas = cur.fetchall()
    values = 'BebidasMermeladas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY RAND() LIMIT 4", (values,))
    BebidasMermeladas = cur.fetchall()
    values = 'Galletas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY RAND() LIMIT 4", (values,))
    Galletas = cur.fetchall()

    # Close Connection
    cur.close()
    return render_template('home.html', tortas=tortas, Anchetas=Anchetas, BebidasMermeladas=BebidasMermeladas, Galletas=Galletas, form=form)


class LoginForm(Form):  # Create Login Form
    username = StringField('', [validators.length(min=1)],
                           render_kw={'autofocus': True, 'placeholder': 'Username'})
    password = PasswordField('', [validators.length(min=3)],
                             render_kw={'placeholder': 'Password'})


# User Login
@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        # GEt user form
        username = form.username.data
        # password_candidate = request.form['password']
        password_candidate = form.password.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

        if result > 0:
            # Get stored value
            data = cur.fetchone()
            password = data['password']
            uid = data['id']
            name = data['name']

            # Compare password
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['uid'] = uid
                session['s_name'] = name
                x = '1'
                cur.execute("UPDATE users SET online=%s WHERE id=%s", (x, uid))

                return redirect(url_for('index'))

            else:
                flash('Incorrect password', 'danger')
                return render_template('login.html', form=form)

        else:
            flash('Username not found', 'danger')
            # Close connection
            cur.close()
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)


@app.route('/out')
def logout():
    if 'uid' in session:
        # Create cursor
        cur = mysql.connection.cursor()
        uid = session['uid']
        x = '0'
        cur.execute("UPDATE users SET online=%s WHERE id=%s", (x, uid))
        session.clear()
        flash('Cerraste sesión', 'success')
        return redirect(url_for('index'))
    return redirect(url_for('login'))


class RegisterForm(Form):
    name = StringField('', [validators.length(min=3, max=50)],
                       render_kw={'autofocus': True, 'placeholder': 'Nombre Completo'})
    username = StringField('', [validators.length(min=3, max=25)], render_kw={'placeholder': 'Usuario'})
    email = EmailField('', [validators.DataRequired(), validators.Email(), validators.length(min=4, max=25)],
                       render_kw={'placeholder': 'Correo Electronico'})
    password = PasswordField('', [validators.length(min=3)],
                             render_kw={'placeholder': 'Contraseña'})
    mobile = StringField('', [validators.length(min=10, max=15)], render_kw={'placeholder': 'Celular'})


@app.route('/register', methods=['GET', 'POST'])
@not_logged_in
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        mobile = form.mobile.data

        # Create Cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password, mobile) VALUES(%s, %s, %s, %s, %s)",
                    (name, email, username, password, mobile))

        # Commit cursor
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Ahora estas registrado puedes iniciar sesión', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)



class OrderForm(Form):  # Create Order Form
    name = StringField('', [validators.length(min=1), validators.DataRequired()],
                       render_kw={'autofocus': True, 'placeholder': 'Nombre Completo'})
    mobile_num = StringField('', [validators.length(min=1), validators.DataRequired()],
                             render_kw={'autofocus': True, 'placeholder': 'Celular'})
    quantity = SelectField('', [validators.DataRequired()],
                           choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    order_place = StringField('', [validators.length(min=1), validators.DataRequired()],
                              render_kw={'placeholder': 'Lugar de entrega'})


@app.route('/tortas', methods=['GET', 'POST'])
def tortas():
    form = OrderForm(request.form)
    # Create cursor
    cur = mysql.connection.cursor()
    # Get message
    values = 'tortas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY id ASC", (values,))
    products = cur.fetchall()
    # Close Connection
    cur.close()
    if 'view' in request.args:
        q = request.args['view']
        productid = q
        x = content_based_filtering(productid)
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM products WHERE id=%s", [q])
        product = curso.fetchall()
        # print('Execution time: ' + str(execution_time) + ' usec')
        if 'uid' in session:
            uid = session['uid']
            # Create cursor
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM product_view WHERE user_id=%s AND product_id=%s", [uid, productid])
            result = cur.fetchall()
            if result:
                now = datetime.datetime.now()
                now_time = now.strftime("%y-%m-%d %H:%M:%S")
                cur.execute("UPDATE product_view SET date=%s WHERE user_id=%s AND product_id=%s",
                            [now_time, uid, productid])
            else:
                cur.execute("INSERT INTO product_view(user_id, product_id) VALUES(%s, %s)", [uid, productid])
                mysql.connection.commit()
        return render_template('view_product.html', x=x, tortass=product)
    elif 'order' in request.args:
        productId = request.args['order']
        cur = mysql.connection.cursor()
        IDD = request.remote_addr
        IDD = IDD.split(".")
        userId = ((int(IDD[0]) * (10 ** 9)) + (int(IDD[1]) * (10 ** 6)) + (int(IDD[2]) * (10 ** 3)) + (int(IDD[3])))
        try:
            cur.execute("INSERT INTO kart0 (userId, productId) VALUES (%s, %s)", [userId, productId])
            msg = "Added successfully"
        except:
            cur.rollback()
            msg = "Error occured"
        cur.close()
    return render_template('tortas.html', tortas=products, form=form)


@app.route('/Anchetas', methods=['GET', 'POST'])
def Anchetas():
    form = OrderForm(request.form)
    # Create cursor
    cur = mysql.connection.cursor()
    # Get message
    values = 'Anchetas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY id ASC", [values])
    products = cur.fetchall()
    # Close Connection
    cur.close()
    if 'view' in request.args:
        q = request.args['view']
        product_id = q
        x = content_based_filtering(product_id)
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM products WHERE id=%s", [q])
        products = curso.fetchall()
        return render_template('view_product.html', x=x, tortass=products)
    elif 'order' in request.args:
        productId = request.args['order']
        cur = mysql.connection.cursor()
        IDD = request.remote_addr
        IDD = IDD.split(".")
        userId = ((int(IDD[0]) * (10 ** 9)) + (int(IDD[1]) * (10 ** 6)) + (int(IDD[2]) * (10 ** 3)) + (int(IDD[3])))
        try:
            cur.execute("INSERT INTO kart0 (userId, productId) VALUES (%s, %s)", [userId, productId])
            msg = "Added successfully"
        except:
            cur.rollback()
            msg = "Error occured"
        cur.close()
    return render_template('Anchetas.html', Anchetas=products, form=form)


@app.route('/BebidasMermeladas', methods=['GET', 'POST'])
def BebidasMermeladas():
    form = OrderForm(request.form)
    # Create cursor
    cur = mysql.connection.cursor()
    # Get message
    values = 'BebidasMermeladas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY id ASC", [values])
    products = cur.fetchall()
    # Close Connection
    cur.close()
    if 'view' in request.args:
        q = request.args['view']
        product_id = q
        x = content_based_filtering(product_id)
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM products WHERE id=%s", [q])
        products = curso.fetchall()
        return render_template('view_product.html', x=x, tortass=products)
    elif 'order' in request.args:
        productId = request.args['order']
        cur = mysql.connection.cursor()
        IDD = request.remote_addr
        IDD = IDD.split(".")
        userId = ((int(IDD[0]) * (10 ** 9)) + (int(IDD[1]) * (10 ** 6)) + (int(IDD[2]) * (10 ** 3)) + (int(IDD[3])))
        try:
            cur.execute("INSERT INTO kart0 (userId, productId) VALUES (%s, %s)", [userId, productId])
            msg = "Added successfully"
        except:
            cur.rollback()
            msg = "Error occured"
        cur.close()
    return render_template('BebidasMermeladas.html', BebidasMermeladas=products, form=form)


@app.route('/Galletas', methods=['GET', 'POST'])
def Galletas():
    form = OrderForm(request.form)
    # Create cursor
    cur = mysql.connection.cursor()
    # Get message
    values = 'Galletas'
    cur.execute("SELECT * FROM products WHERE category=%s ORDER BY id ASC", [values])
    products = cur.fetchall()
    # Close Connection
    cur.close()
    if 'view' in request.args:
        q = request.args['view']
        product_id = q
        x = content_based_filtering(product_id)
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM products WHERE id=%s", [q])
        products = curso.fetchall()
        return render_template('view_product.html', x=x, tortass=products)
    elif 'order' in request.args:
        productId = request.args['order']
        cur = mysql.connection.cursor()
        IDD=request.remote_addr
        IDD=IDD.split(".")
        userId = ((int(IDD[0])*(10**9))+(int(IDD[1])*(10**6))+(int(IDD[2])*(10**3))+(int(IDD[3])))
        try:
            cur.execute("INSERT INTO kart0 (userId, productId) VALUES (%s, %s)", [userId, productId])
            msg = "Added successfully"
        except:
            cur.rollback()
            msg = "Error occured"
        cur.close()
    return render_template('Galletas.html', Galletas=products, form=form)


@app.route('/admin_login', methods=['GET', 'POST'])
@not_admin_logged_in
def admin_login():
    if request.method == 'POST':
        # GEt user form
        username = request.form['email']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM admin WHERE email=%s", [username])

        if result > 0:
            # Get stored value
            data = cur.fetchone()
            password = data['password']
            uid = data['id']
            name = data['firstName']

            # Compare password
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['admin_logged_in'] = True
                session['admin_uid'] = uid
                session['admin_name'] = name

                return redirect(url_for('admin'))

            else:
                flash('Incorrect password', 'danger')
                return render_template('pages/login.html')

        else:
            flash('Username not found', 'danger')
            # Close connection
            cur.close()
            return render_template('pages/login.html')
    return render_template('pages/login.html')


@app.route('/admin_out')
def admin_logout():
    if 'admin_logged_in' in session:
        session.clear()
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin'))


@app.route('/admin')
@is_admin_logged_in
def admin():
    curso = mysql.connection.cursor()
    num_rows = curso.execute("SELECT * FROM products")
    result = curso.fetchall()
    order_rows = curso.execute("SELECT * FROM orders")
    users_rows = curso.execute("SELECT * FROM users")
    return render_template('pages/index.html', result=result, row=num_rows, order_rows=order_rows,
                           users_rows=users_rows)


@app.route('/orders')
@is_admin_logged_in
def orders():
    curso = mysql.connection.cursor()
    num_rows = curso.execute("SELECT * FROM products")
    order_rows = curso.execute("SELECT * FROM orders")
    result = curso.fetchall()
    users_rows = curso.execute("SELECT * FROM users")
    return render_template('pages/all_orders.html', result=result, row=num_rows, order_rows=order_rows,
                           users_rows=users_rows)


@app.route('/users')
@is_admin_logged_in
def users():
    curso = mysql.connection.cursor()
    num_rows = curso.execute("SELECT * FROM products")
    order_rows = curso.execute("SELECT * FROM orders")
    users_rows = curso.execute("SELECT * FROM users")
    result = curso.fetchall()
    return render_template('pages/all_users.html', result=result, row=num_rows, order_rows=order_rows,
                           users_rows=users_rows)



@app.route('/search', methods=['POST', 'GET'])
def search():
    form = OrderForm(request.form)
    if 'q' in request.args:
        q = request.args['q']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get message
        query_string = "SELECT * FROM products WHERE pName LIKE %s ORDER BY id ASC"
        cur.execute(query_string, ('%' + q + '%',))
        products = cur.fetchall()
        # Close Connection
        cur.close()
        flash('Showing result for: ' + q, 'success')
        return render_template('search.html', products=products, form=form)
    else:
        flash('Search again', 'danger')
        return render_template('search.html')

@app.route("/removeFromCart")
def removeFromCart():
    productId = int(request.args.get('productId'))
    print(productId)
    cur = mysql.connection.cursor()
    IDD = request.remote_addr
    IDD = IDD.split(".")
    userId = ((int(IDD[0]) * (10 ** 9)) + (int(IDD[1]) * (10 ** 6)) + (int(IDD[2]) * (10 ** 3)) + (int(IDD[3])))
    try:
        cur.execute("DELETE FROM kart0 WHERE userId = %s AND productId = %s", [userId, productId])
        msg = "removed successfully"
    except:
        msg = "error occured"
        print("hola")
    cur.close()
    cur = mydb.cursor()
    cur.execute(
        "SELECT products.id, products.pName, products.price, products.picture, products.category FROM products, kart0 WHERE products.id = kart0.productId AND kart0.userId = %s",
        [userId])
    products = cur.fetchall()
    totalPrice = 0
    for product in products:
        totalPrice += product[2]
    return render_template("cart.html", products=products, totalPrice=totalPrice)

@app.route("/productDescription")
def productDescription():
    productId = request.args.get('productId')
    cur = mysql.connection.cursor()
    cur.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ?', (productId, ))
    productData = cur.fetchone()
    cur.close()
    return render_template("productDescription.html", data=productData)


@app.route("/addToCart")
def addToCart():
    productId = int(request.args.get('productId'))
    cur = mysql.connection.cursor()
    userId = IIDD
    try:
        cur.execute("INSERT INTO kart0 (userId, productId) VALUES (?, ?)", (userId, productId))
        cur.commit()
        msg = "Added successfully"
    except:
        cur.rollback()
        msg = "Error occured"
    cur.close()
    return redirect(url_for('root'))

@app.route("/cart", methods=['GET', 'POST'])
def cart():
        form = OrderForm(request.form)
        cur = mydb.cursor()
        IDD = request.remote_addr
        IDD = IDD.split(".")
        userId = ((int(IDD[0]) * (10 ** 9)) + (int(IDD[1]) * (10 ** 6)) + (int(IDD[2]) * (10 ** 3)) + (int(IDD[3])))
        cur.execute(
            "SELECT products.id, products.pName, products.price, products.picture, products.category FROM products, kart0 WHERE products.id = kart0.productId AND kart0.userId = %s",
            [userId])
        products = cur.fetchall()
        totalPrice = 0
        for product in products:
            totalPrice += product[2]

        if request.method == 'POST':
            # Parse form data
            email = request.form['email']
            firstName = request.form['firstName']
            lastName = request.form['lastName']
            address1 = request.form['address1']
            address2 = request.form['address2']
            city = request.form['city']
            phone = request.form['phone']

        if request.method == 'POST' and "@" in email and phone.isdigit() and totalPrice!=0:
            name = firstName+" "+lastName
            mobile = phone
            order_place = city+" "+address1+" "+address2
            now = datetime.datetime.now()
            week = datetime.timedelta(days=7)
            delivery_date = now + week
            now_time = delivery_date.strftime("%y-%m-%d %H:%M:%S")
            # Create Cursor
            curs = mysql.connection.cursor()
            for MJS in range(1, 20):
                avaible = firebase.get('/4/data/' + str(MJS - 1), 'available')
                curs.execute("UPDATE products SET available=%s WHERE id=%s", [avaible, MJS])
            for product in products:
                quantity=1
                if 'uid' in session:
                    uid = session['uid']
                    curs.execute("INSERT INTO orders(uid, pid, ofname, mobile, oplace, quantity, ddate, PName) "
                                 "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                                 [uid, product[0], name, mobile, order_place, quantity, now_time,product[1]])
                    curs.execute("UPDATE products SET available=available-%s WHERE id=%s", [quantity, product[0]])
                    curs.execute("SELECT available FROM products WHERE id=%s", [product[0]])
                    avaible = curs.fetchone().get('available')
                    P = '/4/data/' + str(int(product[0]) - 1)
                    firebase.put(P, 'available', avaible)
                else:
                    curs.execute("INSERT INTO orders(pid, ofname, mobile, oplace, quantity, ddate, PName) "
                                 "VALUES(%s, %s, %s, %s, %s, %s, %s)",
                                 [product[0], name, mobile, order_place, quantity, now_time,product[1]])
                    curs.execute("UPDATE products SET available=available-%s WHERE id=%s", [quantity, product[0]])
                    curs.execute("SELECT available FROM products WHERE id=%s", [product[0]])
                    avaible = curs.fetchone().get('available')
                    P = '/4/data/' + str(int(product[0]) - 1)
                    firebase.put(P, 'available', avaible)

            cur.execute(
                "DELETE FROM kart0 WHERE kart0.userId = %s",
                [userId])
            # Commit cursor
            mysql.connection.commit()
            # Close Connection
            cur.close()
            flash('Enseguida nos comunicaremos contigo para efectos de pago', 'success')
            return render_template("cart.html")
        elif request.method == 'POST' and totalPrice!=0:
            flash('Falta información de envío', 'danger')
        elif request.method == 'POST':
            flash('No se ha agregado ningún producto', 'danger')
        return render_template("cart.html", products=products, totalPrice=totalPrice)
        # Parse form data



@app.route('/profile')
@is_logged_in
def profile():
    if 'user' in request.args:
        q = request.args['user']
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM users WHERE id=%s", (q,))
        result = curso.fetchone()
        if result:
            if result['id'] == session['uid']:
                curso.execute("SELECT * FROM orders WHERE uid=%s ORDER BY id ASC", (session['uid'],))
                res = curso.fetchall()
                return render_template('profile.html', result=res)
            else:
                flash('Unauthorised', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Unauthorised! Please login', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Unauthorised', 'danger')
        return redirect(url_for('login'))


class UpdateRegisterForm(Form):
    name = StringField('Nombre Completo', [validators.length(min=3, max=50)],
                       render_kw={'autofocus': True, 'placeholder': 'Nombre Completo'})
    email = EmailField('Email', [validators.DataRequired(), validators.Email(), validators.length(min=4, max=25)],
                       render_kw={'placeholder': 'Correo Electronico'})
    password = PasswordField('Password', [validators.length(min=3)],
                             render_kw={'placeholder': 'Contraseña'})
    mobile = StringField('Mobile', [validators.length(min=10, max=15)], render_kw={'placeholder': 'Celular'})


@app.route('/settings', methods=['POST', 'GET'])
@is_logged_in
def settings():
    form = UpdateRegisterForm(request.form)
    if 'user' in request.args:
        q = request.args['user']
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM users WHERE id=%s", (q,))
        result = curso.fetchone()
        if result:
            if result['id'] == session['uid']:
                if request.method == 'POST' and form.validate():
                    name = form.name.data
                    email = form.email.data
                    password = sha256_crypt.encrypt(str(form.password.data))
                    mobile = form.mobile.data

                    # Create Cursor
                    cur = mysql.connection.cursor()
                    exe = cur.execute("UPDATE users SET name=%s, email=%s, password=%s, mobile=%s WHERE id=%s",
                                      (name, email, password, mobile, q))
                    if exe:
                        flash('Profile updated', 'success')
                        return render_template('user_settings.html', result=result, form=form)
                    else:
                        flash('Profile not updated', 'danger')
                return render_template('user_settings.html', result=result, form=form)
            else:
                flash('Unauthorised', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Unauthorised! Please login', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Unauthorised', 'danger')
        return redirect(url_for('login'))


class DeveloperForm(Form):  #
    id = StringField('', [validators.length(min=1)],
                     render_kw={'placeholder': 'Input a product id...'})


@app.route('/developer', methods=['POST', 'GET'])
def developer():
    form = DeveloperForm(request.form)
    if request.method == 'POST' and form.validate():
        q = form.id.data
        curso = mysql.connection.cursor()
        result = curso.execute("SELECT * FROM products WHERE id=%s", (q,))
        if result > 0:
            x = content_based_filtering(q)
            wrappered = wrappers(content_based_filtering, q)
            execution_time = timeit.timeit(wrappered, number=0)
            seconds = ((execution_time / 1000) % 60)
            return render_template('developer.html', form=form, x=x, execution_time=seconds)
        else:
            nothing = 'Nothing found'
            return render_template('developer.html', form=form, nothing=nothing)
    else:
        return render_template('developer.html', form=form)


# Routes to Render Something
@app.route('/')
def homeW():
    return render_template("home.html")

@app.route('/about', strict_slashes=False)
def about():
    return render_template("about.html")

@app.route('/productos', strict_slashes=False)
def productos():
    return render_template("productos.html")

@app.route('/contacto', strict_slashes=False)
def contacto():
    return render_template("contacto.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0'),
    app.run(debug=True)
