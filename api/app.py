import os
from flask import Flask, jsonify
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.antennes_routes import network_bp
from routes.ia import ia_bp
from routes.incidents_routes import incidents_bp
from routes.reports_routes import reports_bp
from routes.dashboard_routes import admin_bp

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(network_bp)
app.register_blueprint(ia_bp)
app.register_blueprint(incidents_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
