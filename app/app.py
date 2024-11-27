from flask import Flask, render_template
from config import Config
from .models import db
from flask_migrate import Migrate
from .Routes.authentication import authentication
from .Routes.products import products
from .Routes.dashboard import dashboard
from .extensions import mail
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(authentication, url_prefix='')
app.register_blueprint(products, url_prefix='')
app.register_blueprint(dashboard, url_prefix='')

@app.route('/')
async def index():
    return render_template('index.html')

# Convert the Flask app to ASGI
asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    app.run(debug=True)