from flask import Flask
from admin_routes import admin_bp
from user_routes import user_bp
from shared_routes import shared_bp
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '../frontend/templates')
STATIC_DIR = os.path.join(BASE_DIR, '../frontend/static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = 'secret123'

app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(shared_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
