from flask import Flask, render_template
from config import Config
from .models import db
from flask_migrate import Migrate
from .Routes.authentication import authentication
from .Routes.products import products
from .Routes.dashboard import dashboard
from .extensions import mail, initialize_database  # Import from extensions
from asgiref.wsgi import WsgiToAsgi
from flask_jwt_extended import JWTManager
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Global variable to store database pool
db_pool = None

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

@app.before_request
async def startup():
    """
    Initialize database connection pool before first request
    """
    global db_pool
    try:
        db_pool = await initialize_database()
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")

@app.route('/')
async def index():
    global db_pool
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                result = await conn.fetchrow('SELECT current_timestamp')
                print(f"Current database time: {result}")
        except Exception as e:
            logger.error(f"Database query error: {e}")
    
    return render_template('index.html')

@app.teardown_appcontext
async def close_db_pool(exception=None):
    """
    Close the database connection pool when the application shuts down
    """
    global db_pool
    if db_pool:
        try:
            await db_pool.close()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database connection pool: {e}")

# Convert the Flask app to ASGI
asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    app.run(debug=True)