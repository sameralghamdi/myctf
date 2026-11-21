"""Application factory.

create_app() wires config, the SQLite layer, blueprints, Jinja globals and error
handlers, then creates the schema and seeds idempotently so the app is usable the
moment it starts.
"""
from __future__ import annotations

import json
import os
import uuid

from flask import Flask, jsonify, render_template, request

from .config import Config, TestConfig


def create_app(config: type[Config] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config or Config)

    # Give each in-memory test DB its own shared connection key.
    if app.config["DB_PATH"] == ":memory:":
        app.config["_MEM_KEY"] = uuid.uuid4().hex

    from .config import INSTANCE_DIR
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    from . import db
    app.teardown_appcontext(db.close_db)
    db.init_db(app)

    if app.config["TRUST_PROXY"]:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    _register_origin_guard(app)      # must run first: it sets the real client IP
    _register_global_rate_limit(app)
    _register_csrf_guard(app)
    _register_security_headers(app)
    _register_blueprints(app)
    _register_jinja(app)
    _register_errors(app)
    _register_cli(app)

    from .seed import seed_all
    seed_all(app)

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app


def _register_origin_guard(app: Flask) -> None:
    """Reject requests that did not come through the trusted proxy (if configured)."""
    import hmac

    from flask import abort

    @app.before_request
    def _origin_guard():
        secret = app.config["ORIGIN_SECRET"]
        if not secret or request.path == "/healthz":
            return None
        sent = request.headers.get("X-Origin-Secret", "")
        if not hmac.compare_digest(sent.encode(), secret.encode()):
            abort(403)
        # The request is authenticated as coming from our proxy, so its
        # X-Client-IP (the real visitor) can be trusted for rate limits and audit logs.
        client_ip = request.headers.get("X-Client-IP", "").strip()
        if client_ip:
            client_ip = client_ip[:64]
            request.environ["REMOTE_ADDR"] = client_ip
            request.remote_addr = client_ip  # werkzeug fixes this at request creation
        return None


def _register_global_rate_limit(app: Flask) -> None:
    """A ceiling on requests per client IP, across every endpoint. Sensitive
    endpoints (login, register, reset, flag submit, shell) have their own much
    tighter limits; this one stops scrapers and floods."""
    from . import limiter

    @app.before_request
    def _global_limit():
        limit = app.config["RATE_LIMIT_GLOBAL"]
        if limit <= 0 or request.path == "/healthz":
            return None
        if not limiter.allow(f"ip:{request.remote_addr or ''}", limit, 60):
            resp = jsonify({"error": "Too many requests. Please slow down."})
            resp.status_code = 429
            resp.headers["Retry-After"] = "60"
            return resp
        return None


def _register_csrf_guard(app: Flask) -> None:
    """Block cross-site state-changing requests (CSRF), on top of SameSite=Lax.

    Browsers always attach an ``Origin`` header to cross-site POST/PUT/PATCH/
    DELETE. If it is present and is not one of our own origins (or is the
    literal string "null", which sandboxed/opaque pages send), reject it.
    Non-browser clients (curl, tests, scripts) send no Origin and are unaffected;
    they cannot be driven by a victim's browser.
    """
    from flask import abort

    @app.before_request
    def _csrf_guard():
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return None
        origin = request.headers.get("Origin")
        if origin is None:
            return None
        origin = origin.strip().rstrip("/").lower()
        allowed = set(app.config["ALLOWED_ORIGINS"])
        allowed.add(request.host_url.rstrip("/").lower())
        if origin not in allowed:
            abort(403, "Cross-site request blocked.")
        return None


def _register_security_headers(app: Flask) -> None:
    """Headers on every response. The Cloudflare Pages `_headers` file only covers
    static files, so API and lab responses need these from Flask itself."""

    @app.after_request
    def _headers(resp):
        h = resp.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "SAMEORIGIN")  # labs are framed by our own SPA
        h.setdefault("Referrer-Policy", "no-referrer")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if app.config["COOKIE_SECURE"]:
            h.setdefault("Strict-Transport-Security",
                         "max-age=31536000; includeSubDomains")
        path = request.path
        if path.startswith(("/api/", "/admin/api/")):
            # JSON only: nothing here should ever be rendered, framed or cached.
            h.setdefault("Content-Security-Policy",
                         "default-src 'none'; frame-ancestors 'none'")
            h["X-Frame-Options"] = "DENY"
            if not path.startswith("/api/avatars/"):
                h["Cache-Control"] = "no-store"
        elif path.startswith("/labs/"):
            h.setdefault("Cache-Control", "no-store")
            h.setdefault("Content-Security-Policy", "frame-ancestors 'self'")
        return resp


def _register_blueprints(app: Flask) -> None:
    from .auth.routes import bp as auth_bp
    from .core.routes import bp as core_bp
    from .admin.routes import bp as admin_bp
    from .labs.routes import bp as labs_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(labs_bp)


def _register_jinja(app: Flask) -> None:
    from .auth import current_user

    @app.template_filter("sa_time")
    def sa_time(value):
        """Stored UTC "YYYY-MM-DD HH:MM:SS" -> Saudi Arabia time (UTC+3, no DST)."""
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S") + timedelta(hours=3)
        except ValueError:
            return value
        return dt.strftime("%Y-%m-%d %H:%M") + " AST"

    @app.context_processor
    def inject_globals():
        from . import models
        user = current_user()
        # Read-only presentation data for the top-bar score/rank chip shown on
        # every authenticated page. Never mutates state.
        nav_score, nav_rank = 0, 0
        if user is not None:
            try:
                nav_score = models.user_score(user["id"])
                nav_rank = models.user_rank(user["id"])
            except Exception:
                pass
        return {
            "current_user": user,
            "nav_score": nav_score,
            "nav_rank": nav_rank,
            "DIFFICULTY_LABELS": {
                "very_easy": "Very Easy", "easy": "Easy", "medium": "Medium",
                "hard": "Hard", "insane": "Insane",
            },
        }

    @app.template_filter("tojson_safe")
    def tojson_safe(value):
        # Escapes <, >, & and ' so the result can sit inside a <script> block.
        from jinja2.utils import htmlsafe_json_dumps
        return htmlsafe_json_dumps(value)


def _register_errors(app: Flask) -> None:
    def _is_json():
        return (request.path.startswith("/api/")
                or request.path.startswith("/labs/") and request.path.endswith(".json")
                or "application/json" in request.headers.get("Accept", ""))

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(413)
    @app.errorhandler(429)
    def handle(err):
        code = getattr(err, "code", 500)
        if _is_json():
            return jsonify({"error": getattr(err, "description", str(err))}), code
        try:
            return render_template("error.html", code=code,
                                   message=getattr(err, "description", "")), code
        except Exception:
            return (getattr(err, "description", "Error"), code)

    @app.errorhandler(500)
    def handle_500(err):
        if _is_json():
            return jsonify({"error": "internal server error"}), 500
        return render_template("error.html", code=500, message="Server error"), 500


def _register_cli(app: Flask) -> None:
    """Maintenance commands, e.g. inside the container:
    docker compose -f docker-compose.prod.yml --env-file .env.prod exec app flask --app wsgi set-email admin you@example.com
    """
    import click

    @app.cli.command("set-email")
    @click.argument("username")
    @click.argument("email")
    def set_email(username: str, email: str) -> None:
        """Change a user's email (e.g. give the admin a real inbox for sign-in codes)."""
        from . import models
        from .auth.routes import EMAIL_RE
        email = email.strip().lower()
        if not EMAIL_RE.match(email):
            raise click.ClickException("That doesn't look like an email address.")
        user = models.get_user_by_username(username)
        if user is None:
            raise click.ClickException(f"No user named {username!r}.")
        other = models.get_user_by_email(email)
        if other is not None and other["id"] != user["id"]:
            raise click.ClickException("Another account already uses that email.")
        models.set_user_email(user["id"], email)
        models.audit(user["id"], "email_changed_by_cli", f"email={email}")
        click.echo(f"{username}: email set to {email}")
