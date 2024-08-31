from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, fields, Schema

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Elias928@localhost/e_commerce_db'
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
    orders = db.relationship('Order', secondary=order_product, backref=db.backref('products'))


class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'email', 'phone', 'orders')
    orders = fields.Nested('OrderSchema', many=True, exclude=('customer',))

class OrderSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date', 'customer_id', 'products')
    products = fields.Nested('ProductSchema', many=True, exclude=('orders',))

class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'price')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)




with app.app_context():
    db.create_all()

#Add Customer

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
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer)

#Update Customer Info

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

#Delete Customer 

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

#Create CustomerAccount

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
    
#View CustomerAccount

@app.route('/customer_accounts/<int:id>', methods=['GET'])
def get_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    return jsonify({
        'id': account.id,
        'username': account.username,
        'password': account.password,
        'customer': customer_schema.dump(account.customer)
    })


#Update CustomerAccount

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


#Delete CustomerAccount

@app.route('/customer_accounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Customer account removed successfully"}), 200


if __name__ == '__main__':
    app.run(debug=True)