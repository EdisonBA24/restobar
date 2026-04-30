from flask import Flask, jsonify
from flask_cors import CORS
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


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

    # =============================
    # 🔥 DETECTAR ENTORNO
    # =============================
    ENV = os.environ.get("FLASK_ENV", "development")

    # =============================
    # 🔥 CORS CORRECTO
    # =============================
    if ENV == "production":
        CORS(
            app,
            supports_credentials=True,
            origins=[
                "https://restobar.onrender.com"
            ]
        )
    else:
        CORS(app, supports_credentials=True)

    # =============================
    # 🔥 COOKIES (CLAVE PARA LOGIN)
    # =============================
    if ENV == "production":
        app.config["SESSION_COOKIE_SAMESITE"] = "None"
        app.config["SESSION_COOKIE_SECURE"] = True
    else:
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["SESSION_COOKIE_SECURE"] = False

    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # =============================
    # 🔥 EJECUTAR INIT ADMIN (SOLO PRODUCCIÓN)
    # =============================
    if ENV == "production":
        try:
            print("🚀 Inicializando admin...")
            init_admin()  # 🔥 ahora sí controlado
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

    # =============================
    # ROOT
    # =============================
    @app.route("/")
    def home():
        return jsonify({
            "message": "ERP Backend funcionando"
        })

    # =============================
    # ERROR GLOBAL
    # =============================
    @app.errorhandler(Exception)
    def handle_exception(e):
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