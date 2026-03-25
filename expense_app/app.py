import os
from flask import Flask
from flask_login import LoginManager
from models import db, bcrypt, User
from routes.auth import auth_bp
from routes.main import main_bp
from routes.transactions import transactions_bp
from routes.categories import categories_bp
from routes.reports import reports_bp
from routes.budgets import budgets_bp
from routes.insights import insights_bp


def create_app():
    app = Flask(__name__)

    # Configurations
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///expense_manager.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)

    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(insights_bp, url_prefix='/api/insights')

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app


# Run the app (for local + Render deployment)
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 10000))  # Render uses dynamic port
    app.run(host='0.0.0.0', port=port, debug=False)