from flask import Blueprint, jsonify, request
from app.utils.disaster_analytics import DisasterAnalyticsManager

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/disaster-data', methods=['GET'])
def get_disaster_data():
    """Return historical records and last year's disaster data for all types."""
    data = DisasterAnalyticsManager.get_last_year_records()
    return jsonify(data)

@bp.route('/disaster-data/cyclone', methods=['GET'])
@bp.route('/disaster-data/cyclones', methods=['GET'])
def get_cyclone_disaster_data():
    """Return combined IMD cyclone track, wind warning, and cone of uncertainty data."""
    combined = DisasterAnalyticsManager.fetch_all_cyclone_data()
    return jsonify(combined)

@bp.route('/disaster-data/<disaster>', methods=['GET'])
@bp.route('/disaster-data/<disaster>/', methods=['GET'])
def get_specific_disaster_data(disaster):
    """Return disaster-specific data from local /data files."""
    disaster_clean = str(disaster).lower().strip()
    if disaster_clean in ['cyclone', 'cyclones']:
        return jsonify(DisasterAnalyticsManager.fetch_all_cyclone_data())

    import os, json
    from app.utils.disaster_analytics import DATA_DIR
    file_path = os.path.join(DATA_DIR, f"{disaster_clean}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    records = DisasterAnalyticsManager.get_last_year_records()
    return jsonify(records)

@bp.route('/predict/<disaster>', methods=['GET'])
@bp.route('/predict/<disaster>/', methods=['GET'])
def predict_disaster(disaster):
    """Return next year's predicted frequency for a specific disaster."""
    prediction = DisasterAnalyticsManager.predict_next_year(disaster)
    if "error" in prediction:
        return jsonify(prediction), 400
    return jsonify(prediction)

@bp.route('/disaster-data/refresh', methods=['POST'])
def refresh_disaster_data():
    """Trigger dataset refresh and retrain machine learning models."""
    try:
        DisasterAnalyticsManager.fetch_updated_datasets()
        return jsonify({"message": "Disaster datasets refreshed and ML models retrained successfully!", "status": "success"})
    except Exception as e:
        return jsonify({"message": f"Error refreshing datasets: {e}", "status": "error"}), 500

