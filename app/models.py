from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Farmer(db.Model):
    __tablename__ = 'farmers'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    
    products = db.relationship('Product', backref='farmer', lazy=True)  
    orders = db.relationship('Order', backref='farmer', lazy=True)
    
    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Buyer(db.Model):
    __tablename__ = 'buyers'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    
    orders = db.relationship('Order', backref='buyer', lazy=True)
    
    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    price_per_unit = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(), nullable=False)
    amount_available = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'))
    
    order_items = db.relationship('OrderItem', backref='product', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyers.id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_date = db.Column(db.DateTime)
    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending', 'delivered', 'cancelled', 'refunded', name='order_status_enum'),
                       nullable=False, default='pending')
    
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    tracking = db.relationship('OrderTracking', backref='order', lazy=True)
    
    def calculate_total_amount(self):
        return sum(item.calculate_item_total() for item in self.order_items)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Integer, nullable=False)
    
    def calculate_item_total(self):
        return self.quantity * self.price_per_unit


class OrderTracking(db.Model):
    __tablename__ = 'order_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    location = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.String(255), nullable=True)

    def __init__(self, order_id, status, location=None, notes=None):
        self.order_id = order_id
        self.status = status
        self.location = location
        self.notes = notes
