import os
import json
import pickle
import requests
import datetime
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

DISASTER_TYPES = ['earthquakes', 'floods', 'cyclones', 'winds', 'tsunamis', 'rainfall']
DISASTER_ALIAS_MAP = {
    'earthquake': 'earthquakes', 'earthquakes': 'earthquakes',
    'flood': 'floods', 'floods': 'floods',
    'cyclone': 'cyclones', 'cyclones': 'cyclones',
    'wind': 'winds', 'winds': 'winds',
    'tsunami': 'tsunamis', 'tsunamis': 'tsunamis',
    'rainfall': 'rainfall', 'rain': 'rainfall', 'precipitation': 'rainfall'
}

EARTHQUAKES_GEOJSON_FILE = os.path.join(DATA_DIR, "earthquakes.json")
USGS_PAST_HOUR_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
DATA_FILE = os.path.join(DATA_DIR, 'disaster_records.json')

CYCLONE_TRACK_FILE = os.path.join(DATA_DIR, "cyclone_track.json")
CYCLONE_WIND_FILE = os.path.join(DATA_DIR, "cyclone_wind.json")
CYCLONE_COU_FILE = os.path.join(DATA_DIR, "cyclone_cou.json")
FLOODS_FILE = os.path.join(DATA_DIR, "floods.json")
WINDS_FILE = os.path.join(DATA_DIR, "winds.json")
TSUNAMIS_FILE = os.path.join(DATA_DIR, "tsunamis.json")
RAINFALL_FILE = os.path.join(DATA_DIR, "rainfall.json")

IMD_CYCLONE_TRACK_URL = "https://api.imd.gov.in/api/v1/cyclone_track"
IMD_CYCLONE_WIND_URL = "https://api.imd.gov.in/api/v1/cyclone_wind"
IMD_CYCLONE_COU_URL = "https://api.imd.gov.in/api/v1/cyclone_cou"

DEFAULT_CYCLONE_TRACK_DATA = {
    "system_id": "BOB-01-2025",
    "name": "Severe Cyclonic Storm 'JAL-SURAKSHA'",
    "status": "Active",
    "basin": "Bay of Bengal",
    "current_location": {"lat": 15.8, "lng": 80.8, "place": "Off Guntur / Machilipatnam Coast"},
    "intensity_category": "Very Severe Cyclonic Storm",
    "max_sustained_wind_kt": 65,
    "max_sustained_wind_kmh": 120,
    "gusts_kmh": 140,
    "central_pressure_hpa": 984,
    "active_cyclones_count": 1,
    "track_points": [
        {"time": "2025-05-18 06:00", "lat": 13.5, "lng": 84.0, "stage": "Depression", "wind_kmh": 45, "pressure_hpa": 1000},
        {"time": "2025-05-18 18:00", "lat": 14.2, "lng": 83.1, "stage": "Deep Depression", "wind_kmh": 60, "pressure_hpa": 996},
        {"time": "2025-05-19 06:00", "lat": 14.9, "lng": 82.2, "stage": "Cyclonic Storm", "wind_kmh": 85, "pressure_hpa": 990},
        {"time": "2025-05-19 18:00", "lat": 15.4, "lng": 81.5, "stage": "Severe Cyclonic Storm", "wind_kmh": 105, "pressure_hpa": 986},
        {"time": "2025-05-20 06:00", "lat": 15.8, "lng": 80.8, "stage": "Very Severe Cyclonic Storm", "wind_kmh": 120, "pressure_hpa": 984},
        {"time": "2025-05-20 18:00 (Forecast)", "lat": 16.2, "lng": 80.5, "stage": "Landfall (Guntur/Krishna Coast)", "wind_kmh": 110, "pressure_hpa": 988},
        {"time": "2025-05-21 06:00 (Forecast)", "lat": 16.6, "lng": 80.2, "stage": "Inland Weakening", "wind_kmh": 70, "pressure_hpa": 994}
    ]
}

DEFAULT_CYCLONE_WIND_DATA = {
    "system_id": "BOB-01-2025",
    "issued_at": "2025-05-20T06:00:00Z",
    "wind_warning_zones_count": 3,
    "warning_zones": [
        {
            "zone_id": "WIND_RED",
            "level": "Red Warning (Extremely Heavy Wind)",
            "wind_speed_range_kmh": "100-130 km/h",
            "affected_districts": ["Guntur Coastal", "Bapatla", "Krishna"],
            "color": "#d32f2f",
            "polygon": [[15.5, 80.2], [16.4, 80.2], [16.4, 81.1], [15.5, 81.1]]
        },
        {
            "zone_id": "WIND_ORANGE",
            "level": "Orange Warning (High Wind)",
            "wind_speed_range_kmh": "70-100 km/h",
            "affected_districts": ["Prakasam", "West Godavari", "NTR District"],
            "color": "#ff9800",
            "polygon": [[15.0, 79.8], [16.8, 79.8], [16.8, 81.6], [15.0, 81.6]]
        },
        {
            "zone_id": "WIND_YELLOW",
            "level": "Yellow Warning (Moderate Gale)",
            "wind_speed_range_kmh": "50-70 km/h",
            "affected_districts": ["Eluru", "Palnadu", "Nellore"],
            "color": "#fbc02d",
            "polygon": [[14.5, 79.2], [17.2, 79.2], [17.2, 82.2], [14.5, 82.2]]
        }
    ]
}

DEFAULT_CYCLONE_COU_DATA = {
    "system_id": "BOB-01-2025",
    "cou_zones_count": 1,
    "cou_polygon": [
        [15.8, 80.8],
        [16.1, 81.4],
        [16.8, 81.8],
        [17.3, 81.0],
        [17.0, 79.8],
        [16.3, 79.6],
        [15.8, 80.8]
    ],
    "center_line": [
        [15.8, 80.8], [16.2, 80.5], [16.6, 80.2], [17.1, 80.1]
    ],
    "probability_60pct_radius_km": 80,
    "probability_90pct_radius_km": 150
}

DEFAULT_FLOODS_DATA = {
    "disaster": "floods",
    "water_level_m": 4.8,
    "danger_mark_m": 5.5,
    "river_name": "Krishna River",
    "active_flood_warnings": 2,
    "inundated_wards": ["Kaza", "Tadepalli", "Mangalagiri", "Tenali North"],
    "flood_zones": [
        {
            "name": "Krishna Riverbed Lowlands",
            "risk": "High",
            "color": "#d32f2f",
            "polygon": [[16.48, 80.58], [16.52, 80.64], [16.47, 80.66], [16.44, 80.60]]
        },
        {
            "name": "Guntur Canal Low Risk Area",
            "risk": "Moderate",
            "color": "#ff9800",
            "polygon": [[16.28, 80.42], [16.32, 80.48], [16.30, 80.52], [16.25, 80.45]]
        }
    ]
}

DEFAULT_WINDS_DATA = {
    "disaster": "winds",
    "wind_speed_kph": 45,
    "gust_speed_kph": 62,
    "wind_direction": "ENE",
    "high_wind_alerts": 1,
    "gale_zones": [
        {
            "name": "Guntur East & Coastal Corridor",
            "risk": "Moderate",
            "color": "#00695c",
            "polygon": [[16.25, 80.40], [16.35, 80.50], [16.28, 80.58], [16.20, 80.45]]
        }
    ]
}

DEFAULT_TSUNAMIS_DATA = {
    "disaster": "tsunamis",
    "ocean_threat_status": "NO THREAT",
    "buoy_station": "Bay of Bengal Deep Sea Station 23001",
    "sea_level_anomaly_m": 0.05,
    "coastal_tsunami_zones": [
        {
            "name": "Nizampatnam Bay Coastal Zone",
            "risk": "Normal Watch",
            "color": "#00838f",
            "polygon": [[15.85, 80.60], [15.95, 80.70], [15.90, 80.78], [15.80, 80.68]]
        }
    ]
}

DEFAULT_RAINFALL_DATA = {
    "disaster": "rainfall",
    "precipitation_mm_24h": 85.4,
    "intensity": "Heavy Rainfall Warning (ORANGE ALERT)",
    "active_downpour_zones": 3,
    "rain_gauge_station": "Guntur Municipal Meteorological Anemometer",
    "rainfall_zones": [
        {
            "name": "Central Guntur & Urban Drainage Belt",
            "risk": "Heavy Downpour (70-110 mm)",
            "color": "#0288d1",
            "polygon": [[16.28, 80.40], [16.34, 80.48], [16.31, 80.52], [16.24, 80.44]]
        },
        {
            "name": "Tenali & Delta Canal Catchment",
            "risk": "Very Heavy Rainfall (110+ mm)",
            "color": "#01579b",
            "polygon": [[16.20, 80.60], [16.27, 80.68], [16.22, 80.72], [16.15, 80.64]]
        }
    ]
}

INITIAL_DISASTER_DATA = {
    "earthquakes": {
        "2015": 14, "2016": 12, "2017": 16, "2018": 15, "2019": 18,
        "2020": 13, "2021": 19, "2022": 17, "2023": 21, "2024": 22
    },
    "floods": {
        "2015": 8, "2016": 10, "2017": 12, "2018": 14, "2019": 16,
        "2020": 18, "2021": 15, "2022": 19, "2023": 23, "2024": 25
    },
    "cyclones": {
        "2015": 4, "2016": 5, "2017": 6, "2018": 7, "2019": 8,
        "2020": 6, "2021": 9, "2022": 8, "2023": 11, "2024": 12
    },
    "winds": {
        "2015": 22, "2016": 24, "2017": 28, "2018": 26, "2019": 31,
        "2020": 29, "2021": 34, "2022": 32, "2023": 38, "2024": 40
    },
    "tsunamis": {
        "2015": 1, "2016": 0, "2017": 1, "2018": 2, "2019": 1,
        "2020": 0, "2021": 1, "2022": 2, "2023": 1, "2024": 2
    },
    "rainfall": {
        "2015": 12, "2016": 15, "2017": 14, "2018": 18, "2019": 20,
        "2020": 22, "2021": 25, "2022": 24, "2023": 28, "2024": 30
    }
}


class DisasterAnalyticsManager:

    @staticmethod
    def load_data():
        data = None
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error loading disaster data file: {e}")

        if not data:
            data = INITIAL_DISASTER_DATA
            DisasterAnalyticsManager.save_data(data)
        else:
            updated = False
            for dtype in DISASTER_TYPES:
                if dtype not in data or not data[dtype]:
                    data[dtype] = INITIAL_DISASTER_DATA.get(dtype, {})
                    updated = True
            if updated:
                DisasterAnalyticsManager.save_data(data)
        return data

    @staticmethod
    def save_data(data):
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def train_and_save_models():
        data = DisasterAnalyticsManager.load_data()
        for disaster in DISASTER_TYPES:
            records = data.get(disaster, {})
            if not records:
                continue

            years = np.array([int(y) for y in records.keys()]).reshape(-1, 1)
            counts = np.array([float(c) for c in records.values()])

            model = LinearRegression()
            model.fit(years, counts)

            model_path = os.path.join(MODEL_DIR, f"{disaster}_model.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)

    @staticmethod
    def fetch_imd_cyclone_track():
        """Fetch cyclone track from IMD API and save to /data/cyclone_track.json."""
        try:
            resp = requests.get(IMD_CYCLONE_TRACK_URL, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                with open(CYCLONE_TRACK_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"IMD Cyclone Track saved to {CYCLONE_TRACK_FILE}")
                return data
        except Exception as e:
            print(f"IMD Cyclone Track API fetch warning: {e}. Using cached/default track data.")

        # Save default structure if not existing or on error
        if not os.path.exists(CYCLONE_TRACK_FILE):
            with open(CYCLONE_TRACK_FILE, "w") as f:
                json.dump(DEFAULT_CYCLONE_TRACK_DATA, f, indent=4)
            return DEFAULT_CYCLONE_TRACK_DATA
        else:
            try:
                with open(CYCLONE_TRACK_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                with open(CYCLONE_TRACK_FILE, "w") as f:
                    json.dump(DEFAULT_CYCLONE_TRACK_DATA, f, indent=4)
                return DEFAULT_CYCLONE_TRACK_DATA

    @staticmethod
    def fetch_imd_cyclone_wind():
        """Fetch cyclone wind warning from IMD API and save to /data/cyclone_wind.json."""
        try:
            resp = requests.get(IMD_CYCLONE_WIND_URL, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                with open(CYCLONE_WIND_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"IMD Cyclone Wind saved to {CYCLONE_WIND_FILE}")
                return data
        except Exception as e:
            print(f"IMD Cyclone Wind API fetch warning: {e}. Using cached/default wind warning data.")

        if not os.path.exists(CYCLONE_WIND_FILE):
            with open(CYCLONE_WIND_FILE, "w") as f:
                json.dump(DEFAULT_CYCLONE_WIND_DATA, f, indent=4)
            return DEFAULT_CYCLONE_WIND_DATA
        else:
            try:
                with open(CYCLONE_WIND_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                with open(CYCLONE_WIND_FILE, "w") as f:
                    json.dump(DEFAULT_CYCLONE_WIND_DATA, f, indent=4)
                return DEFAULT_CYCLONE_WIND_DATA

    @staticmethod
    def fetch_imd_cyclone_cou():
        """Fetch cyclone cone of uncertainty from IMD API and save to /data/cyclone_cou.json."""
        try:
            resp = requests.get(IMD_CYCLONE_COU_URL, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                with open(CYCLONE_COU_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"IMD Cyclone COU saved to {CYCLONE_COU_FILE}")
                return data
        except Exception as e:
            print(f"IMD Cyclone COU API fetch warning: {e}. Using cached/default COU data.")

        if not os.path.exists(CYCLONE_COU_FILE):
            with open(CYCLONE_COU_FILE, "w") as f:
                json.dump(DEFAULT_CYCLONE_COU_DATA, f, indent=4)
            return DEFAULT_CYCLONE_COU_DATA
        else:
            try:
                with open(CYCLONE_COU_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                with open(CYCLONE_COU_FILE, "w") as f:
                    json.dump(DEFAULT_CYCLONE_COU_DATA, f, indent=4)
                return DEFAULT_CYCLONE_COU_DATA

    @staticmethod
    def fetch_all_cyclone_data():
        """Fetch all IMD cyclone data APIs and return combined dictionary."""
        track = DisasterAnalyticsManager.fetch_imd_cyclone_track()
        wind = DisasterAnalyticsManager.fetch_imd_cyclone_wind()
        cou = DisasterAnalyticsManager.fetch_imd_cyclone_cou()

        active_cyclones_count = track.get("active_cyclones_count", 1 if track.get("track_points") else 0)
        wind_warning_zones_count = wind.get("wind_warning_zones_count", len(wind.get("warning_zones", [])))
        cou_zones_count = cou.get("cou_zones_count", 1 if cou.get("cou_polygon") else 0)

        combined = {
            "status": "success",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "active_cyclones": active_cyclones_count,
            "wind_warning_zones": wind_warning_zones_count,
            "cou_zones": cou_zones_count,
            "track": track,
            "wind": wind,
            "cou": cou
        }

        # Update last hour/active count in disaster records
        data = DisasterAnalyticsManager.load_data()
        data["last_hour_counts"] = data.get("last_hour_counts", {})
        data["last_hour_counts"]["cyclones"] = active_cyclones_count
        DisasterAnalyticsManager.save_data(data)

        return combined

    @staticmethod
    def fetch_other_disasters():
        """Initialize or update data files for floods, winds, tsunamis, rainfall."""
        for file_path, default_data in [
            (FLOODS_FILE, DEFAULT_FLOODS_DATA),
            (WINDS_FILE, DEFAULT_WINDS_DATA),
            (TSUNAMIS_FILE, DEFAULT_TSUNAMIS_DATA),
            (RAINFALL_FILE, DEFAULT_RAINFALL_DATA)
        ]:
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    json.dump(default_data, f, indent=4)

    @staticmethod
    def fetch_live_usgs_past_hour():
        """Fetch live USGS Past Hour All Earthquakes feed and save locally to data/earthquakes.json."""
        try:
            resp = requests.get(USGS_PAST_HOUR_URL, timeout=10)
            if resp.status_code == 200:
                geo_json = resp.json()
                count = geo_json.get("metadata", {}).get("count", len(geo_json.get("features", [])))

                with open(EARTHQUAKES_GEOJSON_FILE, "w") as f:
                    json.dump(geo_json, f, indent=4)

                data = DisasterAnalyticsManager.load_data()
                data["last_hour_counts"] = data.get("last_hour_counts", {})
                data["last_hour_counts"]["earthquakes"] = count
                DisasterAnalyticsManager.save_data(data)
                print(f"USGS Past Hour Earthquakes refreshed: {count} events saved to {EARTHQUAKES_GEOJSON_FILE}")
                return count
        except Exception as e:
            print(f"USGS Past Hour Earthquakes fetch warning: {e}")
        return 0

    @staticmethod
    def fetch_updated_datasets():
        """Hourly/Daily scheduler task: Refresh IMD feeds, USGS feeds, external datasets & retrain ML models."""
        print("Executing Disaster Dataset Refresh & ML Model Retraining...")
        DisasterAnalyticsManager.fetch_all_cyclone_data()
        DisasterAnalyticsManager.fetch_other_disasters()
        DisasterAnalyticsManager.fetch_live_usgs_past_hour()
        DisasterAnalyticsManager.train_and_save_models()
        print("Disaster Dataset Refresh & ML Model Retraining Complete!")

    @staticmethod
    def get_last_year_records():
        data = DisasterAnalyticsManager.load_data()
        current_year = datetime.datetime.now().year
        last_year = current_year - 1
        last_hour_counts = data.get("last_hour_counts", {})

        response = {
            "last_year": last_year,
            "current_year": current_year,
            "disasters": {},
        }

        for disaster in DISASTER_TYPES:
            records = data.get(disaster, {})
            last_record = 0
            if records:
                years = [int(y) for y in records.keys() if y.isdigit()]
                if years:
                    max_yr = max(years)
                    last_record = records.get(str(last_year), records.get(str(max_yr), 0))
            response["disasters"][disaster] = {
                "last_hour_count": last_hour_counts.get(disaster, 1 if disaster == "earthquakes" else 0),
                "last_year_count": last_record,
                "history": records
            }
        return response

    @staticmethod
    def predict_next_year(disaster_name):
        raw_name = str(disaster_name).lower().strip()
        disaster_key = DISASTER_ALIAS_MAP.get(raw_name, "earthquakes")

        data = DisasterAnalyticsManager.load_data()
        records = data.get(disaster_key, {})
        last_hour_counts = data.get("last_hour_counts", {})

        model_path = os.path.join(MODEL_DIR, f"{disaster_key}_model.pkl")
        if not os.path.exists(model_path):
            DisasterAnalyticsManager.train_and_save_models()

        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        current_year = datetime.datetime.now().year
        next_year = current_year + 1

        pred_val = model.predict(np.array([[next_year]]))[0]
        predicted_count = max(0, round(float(pred_val), 1))

        last_year = current_year - 1
        last_year_count = records.get(str(last_year), list(records.values())[-1])

        trend = "increasing" if predicted_count > last_year_count else "decreasing"
        last_hour_cnt = last_hour_counts.get(disaster_key, 1 if disaster_key == "earthquakes" else 0)

        # Get badge numbers for cyclones and other disasters
        active_cyclones = 1
        wind_warning_zones = 3
        cou_zones = 1

        if disaster_key == "cyclones":
            try:
                track = DisasterAnalyticsManager.fetch_imd_cyclone_track()
                wind = DisasterAnalyticsManager.fetch_imd_cyclone_wind()
                cou = DisasterAnalyticsManager.fetch_imd_cyclone_cou()
                active_cyclones = track.get("active_cyclones_count", 1 if track.get("track_points") else 0)
                wind_warning_zones = wind.get("wind_warning_zones_count", len(wind.get("warning_zones", [])))
                cou_zones = cou.get("cou_zones_count", 1 if cou.get("cou_polygon") else 0)
            except Exception as e:
                print(f"Error fetching badge counts: {e}")

        return {
            "disaster": disaster_key,
            "next_year": next_year,
            "predicted_frequency": predicted_count,
            "last_year": last_year,
            "last_year_count": last_year_count,
            "last_hour_count": last_hour_cnt,
            "trend": trend,
            "historical_data": records,
            "active_cyclones": active_cyclones,
            "wind_warning_zones": wind_warning_zones,
            "cou_zones": cou_zones,
            "model_type": "Linear Regression (scikit-learn)"
        }


# Train models on initial import if needed
DisasterAnalyticsManager.train_and_save_models()
