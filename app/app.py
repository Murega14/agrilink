from flask import Flask, render_template
from config import Config
from .models import db
from flask_migrate import Migrate
from .Routes.authentication import authentication
from .Routes.products import products
from .Routes.dashboard import dashboard
from .Routes.user import user
from .Routes.orders import orders
from .extensions import mail, cache
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager()
jwt.init_app(app)
cache.init_app(app)
CORS(app, supports_credentials=True)

# Register blueprints
app.register_blueprint(authentication, url_prefix='')
app.register_blueprint(products, url_prefix='')
app.register_blueprint(dashboard, url_prefix='')
app.register_blueprint(user, url_prefix='')
app.register_blueprint(orders, url_prefix='')


if __name__ == '__main__':
    app.run(debug=True)
