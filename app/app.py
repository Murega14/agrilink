from flask import Flask, render_template
from config import Config
import psycopg2
from .models import db
from flask_migrate import Migrate
from .Routes.authentication import authentication
from .Routes.products import products
from .extensions import mail
from flask_mail import Message


app = Flask(__name__)

app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)

#registering blueprints
app.register_blueprint(authentication, url_prefix='')
app.register_blueprint(products, url_prefix='')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_test_email')
def send_test_email():
    msg = Message('Test Email', sender=app.config['MAIL_USERNAME'], recipients=['recipient@example.com'])
    msg.body = 'This is a test email.'
    try:
        mail.send(msg)
        return "Email sent successfully!"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)