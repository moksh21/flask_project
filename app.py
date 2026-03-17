from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    from routes import auth_routes, password_routes, admin_routes, profile_routes, security_routes

    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(password_routes.password_bp)
    app.register_blueprint(admin_routes.admin_bp)
    app.register_blueprint(profile_routes.profile_bp)
    app.register_blueprint(security_routes.security_bp)

    @app.route("/")
    def index():
        # For now, send users to the login page
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
