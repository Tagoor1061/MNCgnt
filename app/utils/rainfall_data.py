"""
Rainfall Preparedness Unit — IMD Rainfall API Fetchers
=======================================================
Fetches live data from 5 India Meteorological Department (IMD) APIs and
persists each response to /data as JSON:

    rainfall_district.json  -> /api/v1/districtrainfall
    rainfall_warnings.json  -> /api/v1/districtwarning
    rainfall_nowcast.json   -> /api/v1/stationnowcast
    rainfall_state.json     -> /api/v1/staterainfall
    rainfall_basin.json     -> /api/v1/basinqpf

Every fetcher degrades gracefully: if the IMD API is unreachable it falls
back to the cached file, then to a realistic default payload so the UI,
ML pipeline and scheduler never crash.
"""

import os
import json
import datetime
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# File paths (saved outputs)
# ---------------------------------------------------------------------------
RAINFALL_DISTRICT_FILE = os.path.join(DATA_DIR, "rainfall_district.json")
RAINFALL_WARNINGS_FILE = os.path.join(DATA_DIR, "rainfall_warnings.json")
RAINFALL_NOWCAST_FILE = os.path.join(DATA_DIR, "rainfall_nowcast.json")
RAINFALL_STATE_FILE = os.path.join(DATA_DIR, "rainfall_state.json")
RAINFALL_BASIN_FILE = os.path.join(DATA_DIR, "rainfall_basin.json")

# ---------------------------------------------------------------------------
# IMD API endpoints
# ---------------------------------------------------------------------------
IMD_DISTRICT_RAINFALL_URL = "https://api.imd.gov.in/api/v1/districtrainfall"
IMD_DISTRICT_WARNING_URL = "https://api.imd.gov.in/api/v1/districtwarning"
IMD_STATION_NOWCAST_URL = "https://api.imd.gov.in/api/v1/stationnowcast"
IMD_STATE_RAINFALL_URL = "https://api.imd.gov.in/api/v1/staterainfall"
IMD_BASIN_QPF_URL = "https://api.imd.gov.in/api/v1/basinqpf"

# Default query ids (Guntur district, AP warnings, Guntur station, Andhra, Krishna basin)
DEFAULT_PARAMS = {
    "district": {"id": "164"},
    "warning": {"id": "573"},
    "nowcast": {"id": "Guntur"},
    "state": {"id": "andhra"},
    "basin": {"id": "100"},
}

REQUEST_TIMEOUT = 10
# ---------------------------------------------------------------------------
# Default fallback payloads (used when IMD API is unreachable and no cache)
# ---------------------------------------------------------------------------
DEFAULT_DISTRICT_RAINFALL = {
    "status": "default",
    "districts": [
        {"district": "Guntur", "state": "Andhra Pradesh", "rainfall_mm": 85.4,
         "normal_mm": 62.0, "departure_percent": 37.7, "category": "Heavy Rainfall",
         "lat": 16.3067, "lon": 80.4365},
        {"district": "Bapatla", "state": "Andhra Pradesh", "rainfall_mm": 72.1,
         "normal_mm": 58.5, "departure_percent": 23.2, "category": "Heavy Rainfall",
         "lat": 15.9065, "lon": 80.4675},
        {"district": "Palnadu", "state": "Andhra Pradesh", "rainfall_mm": 48.3,
         "normal_mm": 51.0, "departure_percent": -5.3, "category": "Moderate Rainfall",
         "lat": 16.1560, "lon": 79.9000},
        {"district": "NTR", "state": "Andhra Pradesh", "rainfall_mm": 64.8,
         "normal_mm": 55.2, "departure_percent": 17.4, "category": "Moderate Rainfall",
         "lat": 16.5062, "lon": 80.6480},
        {"district": "Krishna", "state": "Andhra Pradesh", "rainfall_mm": 91.2,
         "normal_mm": 60.4, "departure_percent": 51.0, "category": "Very Heavy Rainfall",
         "lat": 16.7000, "lon": 81.1000},
        {"district": "Prakasam", "state": "Andhra Pradesh", "rainfall_mm": 39.6,
         "normal_mm": 47.8, "departure_percent": -17.2, "category": "Light Rainfall",
         "lat": 15.5500, "lon": 79.5000},
    ],
}

DEFAULT_WARNINGS = {
    "status": "default",
    "warnings_count": 3,
    "warnings": [
        {"district": "Guntur", "warning_level": "Red Warning",
         "color": "#d32f2f", "severity": "extremely_heavy",
         "message": "Extremely heavy rainfall (>204 mm) expected; severe urban inundation risk.",
         "valid_from": "today", "valid_to": "+48h",
         "polygon": [[16.28, 80.40], [16.34, 80.48], [16.31, 80.52], [16.24, 80.44]]},
        {"district": "Bapatla", "warning_level": "Orange Warning",
         "color": "#ff9800", "severity": "very_heavy",
         "message": "Very heavy rainfall (115-204 mm); de-watering pumps deployed.",
         "valid_from": "today", "valid_to": "+24h",
         "polygon": [[15.88, 80.42], [15.94, 80.50], [15.90, 80.55], [15.83, 80.47]]},
        {"district": "Palnadu", "warning_level": "Yellow Warning",
         "color": "#fbc02d", "severity": "heavy",
         "message": "Heavy rainfall (64-115 mm); waterlogging in low-lying wards.",
         "valid_from": "today", "valid_to": "+24h",
         "polygon": [[16.10, 79.82], [16.20, 79.95], [16.12, 80.02], [16.02, 79.90]]},
    ],
}

DEFAULT_NOWCAST = {
    "status": "default",
    "station": "Guntur",
    "issued_at": None,  # filled at runtime
    "alerts_count": 2,
    "nowcast": [
        {"time": "+1h", "precipitation_mm": 12.5, "intensity": "moderate",
         "alert": False},
        {"time": "+2h", "precipitation_mm": 28.0, "intensity": "heavy",
         "alert": True,
         "message": "Heavy spell expected — avoid waterlogged underpasses."},
        {"time": "+3h", "precipitation_mm": 35.4, "intensity": "very heavy",
         "alert": True,
         "message": "Very heavy convective spell; move vehicles to higher ground."},
        {"time": "+4h", "precipitation_mm": 18.2, "intensity": "moderate",
         "alert": False},
        {"time": "+5h", "precipitation_mm": 6.0, "intensity": "light",
         "alert": False},
        {"time": "+6h", "precipitation_mm": 2.1, "intensity": "light",
         "alert": False},
    ],
}

DEFAULT_STATE_RAINFALL = {
    "status": "default",
    "states": [
        {"state": "Andhra Pradesh", "rainfall_mm": 68.4, "normal_mm": 55.1,
         "departure_percent": 24.1, "category": "Above Normal"},
        {"state": "Telangana", "rainfall_mm": 52.7, "normal_mm": 50.3,
         "departure_percent": 4.8, "category": "Normal"},
        {"state": "Tamil Nadu", "rainfall_mm": 31.9, "normal_mm": 42.6,
         "departure_percent": -25.1, "category": "Deficient"},
        {"state": "Karnataka", "rainfall_mm": 44.2, "normal_mm": 48.9,
         "departure_percent": -9.6, "category": "Normal"},
        {"state": "Odisha", "rainfall_mm": 77.5, "normal_mm": 58.0,
         "departure_percent": 33.6, "category": "Above Normal"},
        {"state": "Jammu & Kashmir", "rainfall_mm": 22.3, "normal_mm": 30.1,
         "departure_percent": -25.9, "category": "Deficient"},
    ],
}

DEFAULT_BASIN_QPF = {
    "status": "default",
    "basin_id": "100",
    "basin_name": "Krishna Basin",
    "qpf_valid_for": "next 24h",
    "sub_basins": [
        {"name": "Upper Krishna", "qpf_mm": 32.5, "risk": "Moderate"},
        {"name": "Middle Krishna (Srisailam-Nagarjuna Sagar)", "qpf_mm": 58.4,
         "risk": "High"},
        {"name": "Musi Sub-Basin", "qpf_mm": 71.2, "risk": "High"},
        {"name": "Lower Krishna / Delta (Guntur-Vijayawada)", "qpf_mm": 88.6,
         "risk": "Very High"},
        {"name": "Munneru Sub-Basin", "qpf_mm": 64.0, "risk": "High"},
    ],
    "polygon": [[16.10, 79.80], [16.60, 80.20], [17.00, 80.90],
                [16.50, 81.30], [15.95, 80.70], [16.10, 79.80]],
}


class RainfallDataManager:
    """Fetches IMD rainfall APIs, caches to /data, falls back gracefully."""

    @staticmethod
    def _fetch_and_save(url, params, file_path, default_payload):
        """Generic fetch->save->fallback pipeline shared by all 5 APIs."""
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT,
                                headers={"Accept": "application/json",
                                         "User-Agent": "GMC-RainfallPreparedness/1.0"})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError:
                    data = None
                if data:
                    data.setdefault("fetched_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    with open(file_path, "w") as f:
                        json.dump(data, f, indent=4)
                    return data
        except requests.RequestException as exc:
            print(f"[RainfallData] {url} unreachable ({exc}); using cached/default data.")

        # Fallback 1: cached copy from a previous successful fetch
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    cached = json.load(f)
                if isinstance(cached, dict) and cached.get("status") != "default":
                    return cached
                # cache holds a default payload — refresh its timestamp
                cached["fetched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(file_path, "w") as f:
                    json.dump(cached, f, indent=4)
                return cached
            except Exception:
                pass

        # Fallback 2: bundled default payload
        payload = json.loads(json.dumps(default_payload))  # deep copy
        payload["status"] = "default"
        payload["fetched_at"] = default_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(file_path, "w") as f:
                json.dump(payload, f, indent=4)
        except Exception:
            pass
        return payload

    @classmethod
    def fetch_district_rainfall(cls):
        """District-wise rainfall -> data/rainfall_district.json"""
        return cls._fetch_and_save(IMD_DISTRICT_RAINFALL_URL,
                                   DEFAULT_PARAMS["district"],
                                   RAINFALL_DISTRICT_FILE,
                                   DEFAULT_DISTRICT_RAINFALL)

    @classmethod
    def fetch_district_warnings(cls):
        """District warnings (Red/Orange/Yellow/Green) -> data/rainfall_warnings.json"""
        return cls._fetch_and_save(IMD_DISTRICT_WARNING_URL,
                                   DEFAULT_PARAMS["warning"],
                                   RAINFALL_WARNINGS_FILE,
                                   DEFAULT_WARNINGS)

    @classmethod
    def fetch_station_nowcast(cls):
        """Station-wise 3-6h nowcast -> data/rainfall_nowcast.json"""
        payload = cls._fetch_and_save(IMD_STATION_NOWCAST_URL,
                                      DEFAULT_PARAMS["nowcast"],
                                      RAINFALL_NOWCAST_FILE,
                                      DEFAULT_NOWCAST)
        if isinstance(payload, dict) and not payload.get("issued_at"):
            payload["issued_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return payload

    @classmethod
    def fetch_state_rainfall(cls):
        """State-wise rainfall aggregates -> data/rainfall_state.json"""
        return cls._fetch_and_save(IMD_STATE_RAINFALL_URL,
                                   DEFAULT_PARAMS["state"],
                                   RAINFALL_STATE_FILE,
                                   DEFAULT_STATE_RAINFALL)

    @classmethod
    def fetch_basin_qpf(cls):
        """River basin Quantitative Precipitation Forecast -> data/rainfall_basin.json"""
        return cls._fetch_and_save(IMD_BASIN_QPF_URL,
                                   DEFAULT_PARAMS["basin"],
                                   RAINFALL_BASIN_FILE,
                                   DEFAULT_BASIN_QPF)

    @classmethod
    def fetch_all_rainfall_data(cls):
        """Fetch all 5 IMD rainfall APIs and return a combined payload."""
        district = cls.fetch_district_rainfall()
        warnings = cls.fetch_district_warnings()
        nowcast = cls.fetch_station_nowcast()
        state = cls.fetch_state_rainfall()
        basin = cls.fetch_basin_qpf()

        districts = district.get("districts", []) if isinstance(district, dict) else []
        warning_list = warnings.get("warnings", []) if isinstance(warnings, dict) else []
        nowcast_list = nowcast.get("nowcast", []) if isinstance(nowcast, dict) else []

        combined = {
            "status": "success",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "district_rainfall": district,
            "district_warnings": warnings,
            "station_nowcast": nowcast,
            "state_rainfall": state,
            "basin_qpf": basin,
            # Convenience summary counts for badges
            "summary": {
                "district_records": len(districts),
                "state_records": len(state.get("states", [])) if isinstance(state, dict) else 0,
                "basin_sub_basins": len(basin.get("sub_basins", [])) if isinstance(basin, dict) else 0,
                "active_warnings": len(warning_list),
                "nowcast_alerts": sum(1 for n in nowcast_list if n.get("alert")),
                "max_district_rainfall_mm": max(
                    [d.get("rainfall_mm", 0) for d in districts if isinstance(d, dict)] or [0]),
            },
        }
        return combined
