from flask import Blueprint, jsonify, render_template

from app.utils.weather_data import WeatherDataProcessor

bp = Blueprint('weather', __name__)


@bp.route('/weather')
def weather():
    try:
        return jsonify(WeatherDataProcessor.get_weather_summary())
    except Exception as exc:
        return jsonify({
            'status': 'error',
            'message': 'Weather data is temporarily unavailable.',
            'detail': str(exc),
        }), 503


@bp.route('/weather_dashboard')
def weather_dashboard():
    cities_weather = []
    weather_error = None
    try:
        cities_weather = WeatherDataProcessor.get_multi_city_weather()
    except Exception as exc:
        weather_error = str(exc)

    return render_template(
        'weather_dashboard.html',
        cities_weather=cities_weather,
        weather_error=weather_error,
    )

