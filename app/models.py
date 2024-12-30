# models.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

# Define enum types at the database level
product_status_enum = ENUM('available', 'out_of_stock', 'deleted', name='product_status_enum', create_type=False)
order_status_enum = ENUM('pending', 'delivered', 'cancelled', 'refunded', name='order_status_enum', create_type=False)

class BaseModel(db.Model):
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

class UserMixin:
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Farmer(BaseModel, UserMixin):
    __tablename__ = 'farmers'
    
    products = db.relationship('Product', back_populates='farmer', lazy='selectin', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='farmer', lazy='selectin')

class Buyer(BaseModel, UserMixin):
    __tablename__ = 'buyers'
    
    orders = db.relationship('Order', back_populates='buyer', lazy='selectin')

class Product(BaseModel):
    __tablename__ = 'products'
    
    name = db.Column(db.String(100), nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount_available = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(product_status_enum, default='available', nullable=False)
    
    farmer = db.relationship('Farmer', back_populates='products')
    order_items = db.relationship('OrderItem', back_populates='product', lazy='selectin')

class Order(BaseModel):
    __tablename__ = 'orders'
    
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    delivery_date = db.Column(db.DateTime)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(order_status_enum, default='pending', nullable=False)
    
    buyer = db.relationship('Buyer', back_populates='orders')
    farmer = db.relationship('Farmer', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', lazy='selectin', cascade='all, delete-orphan')
    tracking = db.relationship('OrderTracking', back_populates='order', lazy='selectin', cascade='all, delete-orphan')
    
    @property
    def calculate_total_amount(self):
        return sum(item.calculate_item_total for item in self.order_items)

class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')
    
    @property
    def calculate_item_total(self):
        return self.quantity * self.price_per_unit

class OrderTracking(BaseModel):
    __tablename__ = 'order_tracking'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    
    order = db.relationship('Order', back_populates='tracking')
