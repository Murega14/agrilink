from flask import Blueprint, render_template, session, redirect, flash
from ..models import Farmer, Order

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET'])
def view_dashboard():
    user_id = session.get('id')
    user = Farmer.query.filter_by(id=user_id).first()
    if not user:
        flash("Famer not found")
        return redirect('/login/farmer')
    
    pending_orders = Order.query.filter_by(farmers_id=user_id, status='pending').all()
    
    
    return render_template('dashboard.html')