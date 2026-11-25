import os

import click
from flask import Flask, render_template
from datetime import datetime
from config import Config
from .extensions import csrf, db, login_manager, migrate
from .models import utcnow


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .blueprints.main import main_bp
    from .blueprints.auth import auth_bp
    from .blueprints.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Error handlers
    @app.errorhandler(403)
    def forbidden(_):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    register_cli(app)

    @app.template_filter("timesince")
    def timesince(dt):
        """Human-friendly 'x ago' for a naive UTC datetime."""
        if not dt:
            return ""
        seconds = int((utcnow() - dt).total_seconds())
        if seconds < 60:
            return "just now"
        for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
            if seconds >= size:
                return f"{seconds // size}{unit} ago"

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now().year}

    return app


def register_cli(app):
    from .models import User

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed")
    def seed():
        """Create tables and an initial admin user from environment vars."""
        db.create_all()

        email = os.environ.get("ADMIN_EMAIL")
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD")

        if not email or not password:
            raise click.ClickException("Set ADMIN_EMAIL and ADMIN_PASSWORD first.")

        if User.query.filter_by(email=email).first():
            click.echo(f"Admin '{email}' already exists.")
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Created admin user: {email}")
