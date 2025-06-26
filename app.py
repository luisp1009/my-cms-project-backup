from flask import Flask
from admin_routes import admin_bp
from user_routes import user_bp
from shared_routes import shared_bp

app = Flask(__name__)
app.secret_key = 'secret123'

app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(shared_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
