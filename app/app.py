from flask import Flask, render_template
from config import Config
from .models import db
from flask_migrate import Migrate
from .Routes.authentication import authentication
from .Routes.products import products
from .Routes.dashboard import dashboard
from .extensions import mail, initialize_database
from flask_jwt_extended import JWTManager
import asyncio
import logging
import nest_asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nest_asyncio.apply()

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

# Global variable to store database pool
db_pool = None

with app.app_context():
    """
    Initialize database connection pool before first request
    """
    try:
        db_pool = asyncio.run(initialize_database())
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.teardown_appcontext
def close_db_pool(exception=None):
    """
    Close the database connection pool when the application shuts down
    """
    global db_pool
    if db_pool:
        try:
            asyncio.run(db_pool.close())
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database connection pool: {e}")

if __name__ == '__main__':
    app.run(debug=True)