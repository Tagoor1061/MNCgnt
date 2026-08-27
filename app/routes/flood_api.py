"""
Flood Preparedness Unit — API Routes
====================================
Endpoints:
    GET  /api/disaster-data/flood -> combined IMD + Open-Meteo + Google data.
    GET  /api/predict/flood       -> AI flood-risk classification + discharge
                                     forecast with SHAP/LIME explanations.
    POST /api/disaster-data/flood/refresh
                                  -> manual refresh + model retrain trigger.
"""

from flask import Blueprint, jsonify

from app.utils.flood_data import FloodDataManager
from app.utils.flood_ml import predict_flood

bp = Blueprint("flood_api", __name__, url_prefix="/api")


@bp.route("/disaster-data/flood", methods=["GET"])
def get_flood_data():
    """Combined IMD rainfall/QPF + Open-Meteo discharge + Google flood data."""
    try:
        combined = FloodDataManager.fetch_all_flood_data()
        return jsonify(combined)
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@bp.route("/predict/flood", methods=["GET"])
def predict_flood_endpoint():
    """AI/ML flood-risk prediction (classifier + ARIMA + SHAP/LIME)."""
    try:
        return jsonify(predict_flood(include_explanations=True))
    except Exception as exc:
        return jsonify({"error": f"Flood prediction failed: {exc}"}), 500


@bp.route("/disaster-data/flood/refresh", methods=["POST"])
def refresh_flood_data():
    """Manual refresh: re-fetch all flood APIs and retrain the ML models."""
    try:
        combined = FloodDataManager.fetch_all_flood_data()
        from app.utils.flood_ml import train_flood_models

        meta = train_flood_models(force=True)
        return jsonify(
            {
                "status": "success",
                "message": "Flood datasets refreshed and AI models retrained.",
                "classifier": meta.get("classifier_kind"),
                "discharge_model": meta.get("discharge_model_kind"),
                "trained_at": meta.get("trained_at"),
                "summary": combined.get("summary", {}),
            }
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500
