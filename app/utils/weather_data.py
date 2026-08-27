from datetime import datetime

import requests
from flask import current_app


class WeatherDataProcessor:
    # Major Andhra Pradesh cities with coordinates
    AP_CITIES = {
        'Visakhapatnam': {'lat': 17.6869, 'lng': 83.2185},
        'Vizianagaram': {'lat': 18.1205, 'lng': 83.4384},
        'Tirupati': {'lat': 13.1939, 'lng': 79.8965},
        'Anantapur': {'lat': 14.4167, 'lng': 77.6000},
        'Guntur': {'lat': 16.3067, 'lng': 80.4365},
    }

    @staticmethod
    def get_weather_summary():
        """Return current weather for Guntur with fallback provider."""
        lat = current_app.config.get('WEATHER_LATITUDE', 16.3067)
        lon = current_app.config.get('WEATHER_LONGITUDE', 80.4365)
        city = current_app.config.get('WEATHER_CITY', 'Guntur')
        openweather_key = current_app.config.get('OPENWEATHER_API_KEY', '')

        if openweather_key:
            return WeatherDataProcessor._from_openweather(
                lat, lon, city, openweather_key
            )

        return WeatherDataProcessor._from_open_meteo(lat, lon, city)

    @staticmethod
    def get_multi_city_weather():
        """Fetch real-time weather for all 5 major AP cities."""
        cities_weather = []

        for city_name, coords in WeatherDataProcessor.AP_CITIES.items():
            try:
                weather_data = WeatherDataProcessor._from_open_meteo(
                    coords['lat'],
                    coords['lng'],
                    city_name
                )
                cities_weather.append(weather_data)
            except Exception:
                # Add fallback with error message
                cities_weather.append({
                    'status': 'error',
                    'city': city_name,
                    'message': f'Unable to fetch weather for {city_name}',
                    'temperature_c': None,
                    'humidity': None,
                    'wind_kph': None,
                    'condition': 'Data unavailable',
                })

        return cities_weather

    @staticmethod
    def _from_openweather(lat, lon, city, api_key):
        response = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric',
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        weather = data.get('weather') or [{}]
        main = data.get('main') or {}
        wind = data.get('wind') or {}

        return {
            'status': 'ok',
            'provider': 'OpenWeatherMap',
            'city': city,
            'temperature_c': main.get('temp'),
            'humidity': main.get('humidity'),
            'wind_kph': round((wind.get('speed') or 0) * 3.6, 1),
            'condition': weather[0].get('description', 'Unavailable'),
            'updated_at': (
                f"{datetime.utcnow().isoformat()}Z"
            ),
            'requires_api_key': False,
        }

    @staticmethod
    def _from_open_meteo(lat, lon, city):
        response = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': lat,
                'longitude': lon,
                'current': (
                    'temperature_2m,relative_humidity_2m,'
                    'wind_speed_10m,weather_code,is_day'
                ),
            },
            timeout=10,
        )
        response.raise_for_status()
        current = response.json().get('current') or {}

        return {
            'status': 'ok',
            'provider': 'Open-Meteo',
            'city': city,
            'temperature_c': current.get('temperature_2m'),
            'humidity': current.get('relative_humidity_2m'),
            'wind_kph': current.get('wind_speed_10m'),
            'condition': WeatherDataProcessor._weather_code_label(
                current.get('weather_code')
            ),
            'is_day': current.get('is_day', True),
            'updated_at': current.get('time'),
            'requires_api_key': False,
        }

    @staticmethod
    def _weather_code_label(code):
        labels = {
            0: 'Clear sky',
            1: 'Mainly clear',
            2: 'Partly cloudy',
            3: 'Overcast',
            45: 'Fog',
            48: 'Depositing rime fog',
            51: 'Light drizzle',
            53: 'Moderate drizzle',
            55: 'Dense drizzle',
            61: 'Slight rain',
            63: 'Moderate rain',
            65: 'Heavy rain',
            80: 'Rain showers',
            95: 'Thunderstorm',
        }
        return labels.get(code, 'Weather data available')

    @staticmethod
    def get_weather_icon(condition, is_day=True):
        """Return emoji/icon based on weather condition."""
        condition_lower = condition.lower() if condition else ''

        if 'clear' in condition_lower:
            return '☀️' if is_day else '🌙'
        elif 'cloudy' in condition_lower or 'overcast' in condition_lower:
            return '☁️'
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return '🌧️'
        elif 'storm' in condition_lower:
            return '⛈️'
        elif 'fog' in condition_lower:
            return '🌫️'
        else:
            return '🌤️'
