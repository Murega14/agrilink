from flask import Flask, render_template
from config import Config
from .models import db
from flask_migrate import Migrate
from .Routes.authentication import authentication
from .Routes.products import products
from .Routes.dashboard import dashboard
from .extensions import mail
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager()
jwt.init_app(app)

# Register blueprints
app.register_blueprint(authentication, url_prefix='')
app.register_blueprint(products, url_prefix='')
app.register_blueprint(dashboard, url_prefix='')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)