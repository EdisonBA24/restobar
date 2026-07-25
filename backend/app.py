from flask import Flask, jsonify, send_from_directory
from pathlib import Path
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import os

# 🔥 NUEVO: importar tu script
from init_admin import init_admin

from routes.productos import productos_bp
from routes.unidades import unidades_bp
from routes.health import health_bp
from routes.compras import compras_bp 
from routes.recetas import recetas_bp
from routes.insumos import insumos_bp
from routes.ventas import ventas_bp
from routes.costos import costos_bp
from routes.dashboard import dashboard_bp
from routes.reportes import reportes_bp
from routes.auth import auth_bp
from routes.pedidos import pedidos_bp
from routes.clientes import clientes_bp
from routes.usuarios import usuarios_bp
from routes.pagos import pagos_bp
from routes.proveedores import proveedores_bp

# =============================
# FRONTEND
# =============================
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


def create_app():
    app = Flask(
        __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
    )
    app.json.sort_keys = False
    app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

    from datetime import timedelta

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
    app.config["SESSION_USE_SIGNER"] = True

    # =============================
    # 🔥 DETECTAR ENTORNO
    # =============================
    ENV = os.environ.get("FLASK_ENV", "development")

    # 🔥 NUEVO: detectar si está en Render
    IS_RENDER = os.environ.get("RENDER_SERVICE_ID") is not None

    # =============================
    # 🔥 CORS CORRECTO
    # =============================
    if ENV == "production" or IS_RENDER:
        CORS(
            app,
            supports_credentials=True,
            origins=[
                "https://restobar.onrender.com",
                #"https://frontend-restobar.onrender.com",
                "http://localhost:5500",
                "http://localhost:5000",
                "http://127.0.0.1:5500",
                "http://127.0.0.1:5000"
            ]
        )
    else:
        CORS(app, supports_credentials=True)

    # =============================
    # 🔥 COOKIES (CLAVE PARA LOGIN)
    # =============================
    if ENV == "production" or IS_RENDER:
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["SESSION_COOKIE_SECURE"] = True
        #app.config["SESSION_COOKIE_NAME"] = "restobar_session"
        #app.config["SESSION_COOKIE_DOMAIN"] = ".onrender.com"
    else:
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["SESSION_COOKIE_SECURE"] = False

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_REFRESH_EACH_REQUEST"] = False

    # =============================
    # 🔥 EJECUTAR INIT ADMIN (PRODUCCIÓN / RENDER)
    # =============================
    if ENV == "production" or IS_RENDER:
        try:
            print("🚀 Inicializando admin...")
            init_admin()
        except Exception as e:
            print("❌ Error init admin:", e)

    # =============================
    # BLUEPRINTS
    # =============================
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(productos_bp, url_prefix="/api")
    app.register_blueprint(unidades_bp, url_prefix="/api")
    app.register_blueprint(compras_bp, url_prefix="/api")
    app.register_blueprint(recetas_bp, url_prefix="/api")
    app.register_blueprint(insumos_bp, url_prefix="/api")
    app.register_blueprint(ventas_bp, url_prefix="/api")
    app.register_blueprint(costos_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(reportes_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(pedidos_bp, url_prefix="/api")
    app.register_blueprint(clientes_bp, url_prefix="/api")
    app.register_blueprint(usuarios_bp, url_prefix="/api")
    app.register_blueprint(pagos_bp, url_prefix="/api")
    app.register_blueprint(proveedores_bp, url_prefix="/api")

    # =============================
    # 🔥 SERVIR FRONTEND
    # =============================

    @app.route("/")
    def frontend_index():
        return send_from_directory(FRONTEND_DIR, "index.html")
    
    @app.route("/pages/<path:filename>")
    def frontend_pages(filename):
        return send_from_directory(FRONTEND_DIR / "pages", filename)
    
    @app.route("/js/<path:filename>")
    def frontend_js(filename):
        return send_from_directory(FRONTEND_DIR / "js", filename)
    
    @app.route("/js/models/<path:filename>")
    def frontend_js_models(filename):
        return send_from_directory(FRONTEND_DIR / "js/models", filename)
    
    @app.route("/css/<path:filename>")
    def frontend_css(filename):
        return send_from_directory(FRONTEND_DIR / "css", filename)
    
    @app.route("/assets/<path:filename>")
    def frontend_assets(filename):
        return send_from_directory(FRONTEND_DIR / "assets", filename)
    
    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(FRONTEND_DIR / "assets", "logo.ico")
    
    @app.route("/<path:path>")
    def frontend(path):

        archivo = FRONTEND_DIR / path

        if archivo.exists():
            return send_from_directory(FRONTEND_DIR, path)

        return send_from_directory(FRONTEND_DIR, "index.html")

    # =============================
    # ROOT
    # =============================
    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "message": "ERP Backend funcionando"
        })
    # @app.route("/")
    # def home():
    #    return jsonify({
    #        "message": "ERP Backend funcionando"
    #    })

    # =============================
    # ERROR GLOBAL
    # =============================

    @app.errorhandler(Exception)
    def handle_exception(e):

        # Permitir que los errores HTTP (404, 405, etc.)
        # mantengan su código original.
        if isinstance(e, HTTPException):
            return jsonify({
                "status": "error",
                "message": e.description
            }), e.code

        # Errores reales del servidor
        import traceback

        print("\n========== ERROR ==========")
        traceback.print_exc()
        print("===========================\n")

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    return app


# 🔥 RENDER ENTRYPOINT
app = create_app()


# 🔥 LOCAL RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)