"""
Rainfall Preparedness Unit — API Routes
=======================================
Endpoints:
    GET /api/disaster-data/rainfall  -> combined IMD rainfall + warnings +
                                        nowcast + basin QPF forecast.
    GET /api/predict/rainfall        -> AI (LSTM/SARIMA) heavy-rainfall
                                        prediction with SHAP/LIME explanations.
    POST /api/disaster-data/rainfall/refresh
                                     -> manual refresh + model retrain trigger.
"""

from flask import Blueprint, jsonify

from app.utils.rainfall_data import RainfallDataManager
from app.utils.rainfall_ml import predict_rainfall

bp = Blueprint('rainfall_api', __name__, url_prefix='/api')


@bp.route('/disaster-data/rainfall', methods=['GET'])
def get_rainfall_data():
    """Combined IMD rainfall + warnings + nowcast + river-basin QPF."""
    try:
        combined = RainfallDataManager.fetch_all_rainfall_data()
        return jsonify(combined)
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@bp.route('/predict/rainfall', methods=['GET'])
def predict_rainfall_endpoint():
    """AI/ML heavy-rainfall prediction (LSTM + SARIMA + SHAP/LIME)."""
    try:
        return jsonify(predict_rainfall(include_explanations=True))
    except Exception as exc:
        return jsonify({"error": f"Rainfall prediction failed: {exc}"}), 500


@bp.route('/disaster-data/rainfall/refresh', methods=['POST'])
def refresh_rainfall_data():
    """Manual refresh: re-fetch all 5 IMD APIs and retrain the ML models."""
    try:
        combined = RainfallDataManager.fetch_all_rainfall_data()
        from app.utils.rainfall_ml import train_rainfall_models
        meta = train_rainfall_models(force=True)
        return jsonify({
            "status": "success",
            "message": "IMD rainfall datasets refreshed and AI models retrained.",
            "model": meta.get("model_kind"),
            "trained_at": meta.get("trained_at"),
            "summary": combined.get("summary", {}),
        })
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500
