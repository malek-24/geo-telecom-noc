import os, time, json, random, io
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, send_file
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import JWT_SECRET, JWT_EXPIRATION_HOURS, ADMIN_LOGS, SYSTEM_SETTINGS
from auth.decorators import token_required, admin_required, role_required
from ia.prediction import run_ai_prediction, get_ia_report_anomalies
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


ia_bp = Blueprint('ia_bp', __name__)

@ia_bp.route("/predict", methods=["GET"])
@token_required
def predict():
    return run_ai_prediction()

@ia_bp.route("/internal/predict", methods=["GET"])
def get_internal_ia_predictions():
    return run_ai_prediction()

