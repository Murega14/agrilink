from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config
import psycopg2
from .models import db
from .Routes.authentication import authentication

app = Flask(__name__)

app.config.from_object(Config)
db.init_app(app)

#registering blueprints
app.register_blueprint(authentication, url_prefix='/')

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)