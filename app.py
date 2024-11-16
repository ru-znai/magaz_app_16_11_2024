from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Для работы с сессиями
db = SQLAlchemy(app)


# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)


# Глобальная переменная корзины (сессия для каждого пользователя)
@app.before_request
def before_request():
    if 'cart' not in session:
        session['cart'] = {}


# Маршрут для главной страницы
@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
    else:
        username = None
    return render_template('index.html', username=username)


# Маршрут для логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Неверный логин или пароль', 401
    return render_template('login.html')


# Маршрут для логаута
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


# Маршрут для регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


# API для получения списка товаров
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'quantity': p.quantity,
        'image_url': p.image_url
    } for p in products])


# API для добавления товара в корзину
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Для добавления в корзину нужно войти в систему.'})

    product_id = request.json.get('id')
    product = Product.query.get(product_id)
    if product and product.quantity > 0:
        cart = session['cart']
        if product_id in cart:
            if cart[product_id] < product.quantity:
                cart[product_id] += 1
            else:
                return jsonify({'success': False, 'message': 'Товар в корзине достиг предела по наличию.'})
        else:
            cart[product_id] = 1
        session['cart'] = cart
        return jsonify({'success': True, 'message': 'Товар добавлен в корзину.'})
    return jsonify({'success': False, 'message': 'Товар недоступен.'})


# API для получения содержимого корзины
@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Для доступа к корзине нужно войти в систему.'})

    cart_items = []
    cart = session['cart']
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'available': product.quantity
            })
    return jsonify(cart_items)


# API для оформления заказа
@app.route('/api/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Для оформления заказа нужно войти в систему.'})

    cart = session['cart']
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product and product.quantity >= quantity:
            product.quantity -= quantity
        else:
            return jsonify(
                {'success': False, 'message': f'Товар "{product.name}" закончился или недостаточно в наличии.'})
    db.session.commit()
    session['cart'] = {}  # Очистить корзину после оформления
    return jsonify({'success': True, 'message': 'Покупка успешно завершена!'})


# Инициализация базы данных вручную
def setup_database():
    with app.app_context():
        db.create_all()
        if not Product.query.first():
            db.session.add_all([
                Product(name="Ноутбук", price=1000, quantity=5, image_url="https://via.placeholder.com/150"),
                Product(name="Смартфон", price=500, quantity=10, image_url="https://via.placeholder.com/150"),
                Product(name="Наушники", price=100, quantity=0, image_url="https://via.placeholder.com/150"),
            ])
            db.session.commit()


if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
