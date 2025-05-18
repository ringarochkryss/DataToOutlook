from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Get database URL from .env, else use sqlite as fallback
db_url = os.getenv('DATABASE_URL', 'sqlite:///exports.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import models after db is defined (optional, but good for migrations)
from ImportDataToOutlook import models

# Import views after app and db are defined
from ImportDataToOutlook import views