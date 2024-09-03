from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, fields, Schema

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:placeholder@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders = db.relationship('Order', backref='customer')


class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  
    expected_delivery_date = db.Column(db.Date)  
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))


class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)


order_product = db.Table('Order_Product',
    db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True)
)

class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    orders = db.relationship('Order', secondary=order_product, backref=db.backref('products'))

class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'email', 'phone', 'orders')
    orders = fields.Nested('OrderSchema', many=True)

class OrderSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date', 'customer_id', 'products')
    products = fields.Nested('ProductSchema', many=True)

class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'price', 'stock')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

with app.app_context():
    db.create_all()

# Add Customer
@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_customer = Customer(name=customer_data['name'],
                            email=customer_data['email'],
                            phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "New customer added successfully"}), 201

# View Customer
@app.route('/customers/<int:id>', methods=['GET'])
def get_customer(id):
    print(f"Fetching customer with ID: {id}")
    customer = Customer.query.get_or_404(id)
    print(f"Customer found: {customer.name}")
    return customer_schema.jsonify(customer)

# Update Customer Info
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

# Delete Customer 
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

# Create CustomerAccount
@app.route('/customer_accounts', methods=['POST'])
def add_customer_account():
    try:
        account_data = request.json
        customer_id = account_data['customer_id']
        customer = Customer.query.get_or_404(customer_id)
        
        new_account = CustomerAccount(username=account_data['username'],
                                      password=account_data['password'],
                                      customer=customer)
        
        db.session.add(new_account)
        db.session.commit()
        return jsonify({"message": "New customer account added successfully"}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    
# View CustomerAccount
@app.route('/customer_accounts/<int:id>', methods=['GET'])
def get_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    return jsonify({
        'id': account.id,
        'username': account.username,
        'password': account.password,
        'customer': customer_schema.dump(account.customer)
    })

# Update CustomerAccount
@app.route('/customer_accounts/<int:id>', methods=['PUT'])
def update_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    try:
        account_data = request.json
        account.username = account_data['username']
        account.password = account_data['password']
        db.session.commit()
        return jsonify({"message": "Customer account updated successfully"}), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

# Delete CustomerAccount
@app.route('/customer_accounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Customer account removed successfully"}), 200

# Add Product Endpoint
@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_product = Product(name=product_data['name'],
                          price=product_data['price'],
                          stock=product_data.get('stock', 0))
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "New product added successfully"}), 201

# View Product 
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)

# Update Product
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']
    product.stock = product_data['stock']
    db.session.commit()
    return jsonify({"message": "Product details updated successfully"}), 200

# Delete Product
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product removed successfully"}), 200

# List all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

# Update Stock
@app.route('/products/<int:id>/stock', methods=['PUT'])
def update_stock(id):
    product = Product.query.get_or_404(id)
    try:
        stock_data = request.json
        product.stock = stock_data['stock']
        db.session.commit()
        return jsonify({"message": "Product stock updated successfully"}), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

# Restock Products
@app.route('/products/restock', methods=['POST'])
def restock_products():
    threshold = request.json.get('threshold', 10)
    restock_amount = request.json.get('restock_amount', 50)
    
    products = Product.query.filter(Product.stock < threshold).all()
    for product in products:
        product.stock += restock_amount
    
    db.session.commit()
    return jsonify({"message": "Products restocked successfully"}), 200



# Place Order
@app.route('/orders', methods=['POST'])
def place_order():
    try:
        order_data = request.json
        customer_id = order_data['customer_id']
        product_ids = order_data['product_ids']
        
        customer = Customer.query.get_or_404(customer_id)
        new_order = Order(date=order_data['date'], customer=customer)
        
        for product_id in product_ids:
            product = Product.query.get_or_404(product_id)
            new_order.products.append(product)
        
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"message": "Order placed successfully"}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    


# Retrieve Order
@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return order_schema.jsonify(order)



# Track Order
@app.route('/orders/<int:id>/status', methods=['GET'])
def track_order(id):
    order = Order.query.get_or_404(id)
    return jsonify({
        'id': order.id,
        'date': order.date,
        'status': order.status,  
        'expected_delivery_date': order.expected_delivery_date
    })



# Manage Order History
@app.route('/customers/<int:customer_id>/orders', methods=['GET'])
def get_order_history(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer.id).all()
    return orders_schema.jsonify(orders)


# Cancel Order
@app.route('/orders/<int:id>/cancel', methods=['PUT'])
def cancel_order(id):
    order = Order.query.get_or_404(id)
    if order.status != 'shipped' and order.status != 'completed':  
        order.status = 'canceled'
        db.session.commit()
        return jsonify({"message": "Order canceled successfully"}), 200
    else:
        return jsonify({"message": "Order cannot be canceled"}), 400
    

# Calculate Order Total Price
@app.route('/orders/<int:id>/total', methods=['GET'])
def calculate_order_total(id):
    order = Order.query.get_or_404(id)
    total_price = sum(product.price for product in order.products)
    return jsonify({'total_price': total_price})


if __name__ == '__main__':
    app.run(debug=True)
