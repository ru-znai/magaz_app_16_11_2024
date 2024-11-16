from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель товара
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

# Глобальная переменная корзины
cart = {}

# Маршрут для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

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
    product_id = request.json.get('id')
    product = Product.query.get(product_id)
    if product and product.quantity > 0:
        if product_id in cart:
            if cart[product_id] < product.quantity:
                cart[product_id] += 1
                return jsonify({'success': True, 'message': 'Количество товара увеличено.'})
            else:
                return jsonify({'success': False, 'message': 'Товар в корзине достиг предела по наличию.'})
        else:
            cart[product_id] = 1
            return jsonify({'success': True, 'message': 'Товар добавлен в корзину.'})
    return jsonify({'success': False, 'message': 'Товар недоступен.'})

# API для получения содержимого корзины
@app.route('/api/cart', methods=['GET'])
def get_cart():
    cart_items = []
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

# API для обновления количества товара в корзине
@app.route('/api/cart/<int:product_id>', methods=['PUT'])
def update_cart(product_id):
    quantity = request.json.get('quantity')
    product = Product.query.get(product_id)
    if product and product.quantity >= quantity >= 0:
        if quantity == 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = quantity
        return jsonify({'success': True, 'message': 'Корзина обновлена.'})
    return jsonify({'success': False, 'message': 'Невозможно обновить корзину: превышение наличия товара.'})

# API для оформления заказа
@app.route('/api/checkout', methods=['POST'])
def checkout():
    global cart
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product and product.quantity >= quantity:
            product.quantity -= quantity
        else:
            return jsonify({'success': False, 'message': f'Товар "{product.name}" закончился или недостаточно в наличии.'})
    db.session.commit()
    cart = {}
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
