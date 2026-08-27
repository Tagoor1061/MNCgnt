"""
Flood Preparedness Unit — IMD + Open-Meteo + Google Flood API Fetchers
======================================================================
Fetches live data from 3 sources and persists each response to /data:

    flood_discharge.json -> Open-Meteo Flood API (river discharge)
    flood_qpf.json       -> IMD basin QPF + district/state rainfall

IMD APIs:
    /api/v1/districtrainfall -> district rainfall (flood driver)
    /api/v1/staterainfall    -> state rainfall aggregate
    /api/v1/basinqpf         -> river basin Quantitative Precipitation Forecast

Open-Meteo Flood API:
    https://flood-api.open-meteo.com/v1/flood?latitude=..&longitude=..
        &daily=river_discharge
    Returns river_discharge plus mean/median/max/min/p25/p75 statistics.

Google Flood Forecasting API (gauge-based):
    flashFloods:search
    floodStatus:queryLatestFloodStatusByGaugeIds
    floodStatus:searchLatestFloodStatusByArea
    gauges:queryGaugeForecasts

Every fetcher degrades gracefully: live API -> cached file -> bundled
default payload, so the UI, ML pipeline and scheduler never crash.
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
FLOOD_DISCHARGE_FILE = os.path.join(DATA_DIR, "flood_discharge.json")
FLOOD_QPF_FILE = os.path.join(DATA_DIR, "flood_qpf.json")

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
IMD_DISTRICT_RAINFALL_URL = "https://api.imd.gov.in/api/v1/districtrainfall"
IMD_STATE_RAINFALL_URL = "https://api.imd.gov.in/api/v1/staterainfall"
IMD_BASIN_QPF_URL = "https://api.imd.gov.in/api/v1/basinqpf"

OPEN_METEO_FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
GOOGLE_FLOOD_BASE = "https://floodforecasting.googleapis.com/v1"

REQUEST_TIMEOUT = 10

# Guntur, Andhra Pradesh — Krishna delta region
DEFAULT_LAT, DEFAULT_LON = 16.3067, 80.4365

DEFAULT_PARAMS = {
    "district": {"id": "573"},
    "state": {"id": "andhra"},
}

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "GMC-FloodPreparedness/1.0",
}

# ---------------------------------------------------------------------------
# Default fallback payloads (used when APIs are unreachable and no cache)
# ---------------------------------------------------------------------------
DEFAULT_DISCHARGE = {
    "status": "default",
    "latitude": DEFAULT_LAT,
    "longitude": DEFAULT_LON,
    "river": "Krishna",
    "daily": {
        "time": [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(6, -1, -1)],
        "river_discharge": [420.5, 455.2, 512.8, 604.1, 738.6, 812.3, 889.0],
    },
    "statistics": {"mean": 633.2, "median": 604.1, "max": 889.0,
                   "min": 420.5, "p25": 484.0, "p75": 775.5},
}

DEFAULT_QPF = {
    "status": "default",
    "basin_qpf": {
        "basin_name": "Krishna Basin (Lower)",
        "issued_at": None,
        "polygon": [[16.05, 80.10], [16.35, 80.30], [16.20, 80.65], [15.90, 80.40]],
        "sub_basins": [
            {"name": "Krishna Delta", "qpf_mm": 96.4, "risk": "HIGH"},
            {"name": "Munneru Tributary", "qpf_mm": 64.2, "risk": "MODERATE"},
            {"name": "Budameru Channel", "qpf_mm": 42.8, "risk": "MODERATE"},
        ],
    },
    "district_rainfall": {
        "districts": [
            {"district": "Guntur", "rainfall_mm": 118.6, "normal_mm": 62.1,
             "departure_percent": 91.0, "category": "Very Heavy",
             "lat": 16.3067, "lon": 80.4365},
            {"district": "Bapatla", "rainfall_mm": 96.2, "normal_mm": 58.4,
             "departure_percent": 64.7, "category": "Heavy",
             "lat": 15.9049, "lon": 80.4675},
            {"district": "Palnadu", "rainfall_mm": 54.7, "normal_mm": 44.0,
             "departure_percent": 24.3, "category": "Moderate",
             "lat": 16.1067, "lon": 79.9365},
        ],
    },
    "state_rainfall": {
        "state": "Andhra Pradesh",
        "actual_mm": 74.8, "normal_mm": 51.2, "departure_percent": 46.1,
    },
    # Google Flood Forecasting API gauges (fallback snapshot)
    "gauges": [
        {"gauge_id": "hybasin_31013", "site_name": "Vijayawada (Prakasam Barrage)",
         "lat": 16.5033, "lon": 80.6165,
         "status": "ABOVE_NORMAL", "discharge_m3s": 812.3,
         "forecast_peak_m3s": 940.0, "forecast_time": "+24h",
         "message": "River rising; bund strengthening advised along low-lying stretches."},
        {"gauge_id": "hybasin_31027", "site_name": "Tenali Canal Gauge",
         "lat": 16.2389, "lon": 80.6448,
         "status": "NORMAL", "discharge_m3s": 210.5,
         "forecast_peak_m3s": 245.0, "forecast_time": "+24h",
         "message": "Stable flow within normal monsoon range."},
    ],
    "flash_floods": [
        {"area": "Guntur — Krishna delta lowlands", "severity": "MODERATE",
         "probability_percent": 55, "valid_from": "today", "valid_to": "+36h",
         "polygon": [[16.20, 80.35], [16.32, 80.48], [16.25, 80.58], [16.12, 80.44]],
         "message": "Flash-flood watch: intense rain may cause rapid runoff in urban drains."},
    ],
}

# ---------------------------------------------------------------------------
# Flood-risk thresholds on river discharge (m³/s) for the Krishna delta scale
# ---------------------------------------------------------------------------
DISCHARGE_MODERATE = 500.0   # m³/s — banks approaching capacity
DISCHARGE_HIGH = 750.0       # m³/s — floodplain inundation begins
DISCHARGE_EXTREME = 1000.0   # m³/s — severe inundation, evacuation likely

FLOOD_RISK_COLORS = {"LOW": "#2e7d32", "MODERATE": "#fbc02d",
                     "HIGH": "#FFA500", "EXTREME": "#FF0000"}


def _risk_from_discharge(q):
    if q >= DISCHARGE_EXTREME:
        return "EXTREME"
    if q >= DISCHARGE_HIGH:
        return "HIGH"
    if q >= DISCHARGE_MODERATE:
        return "MODERATE"
    return "LOW"


class FloodDataManager:
    """Fetches IMD + Open-Meteo + Google flood APIs, caches to /data."""

    # -- generic fetch->save->fallback pipeline -----------------------------
    @staticmethod
    def _fetch_and_save(url, params, file_path, default_payload):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT,
                                headers=REQUEST_HEADERS)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError:
                    data = None
                if data:
                    data.setdefault("fetched_at", datetime.datetime.now()
                                    .strftime("%Y-%m-%d %H:%M:%S"))
                    with open(file_path, "w") as f:
                        json.dump(data, f, indent=4)
                    return data
        except requests.RequestException as exc:
            print(f"[FloodData] {url} unreachable ({exc}); using cached/default data.")

        # Fallback 1: cached copy from a previous successful fetch
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    cached = json.load(f)
                if isinstance(cached, dict) and cached.get("status") != "default":
                    return cached
                cached["fetched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(file_path, "w") as f:
                    json.dump(cached, f, indent=4)
                return cached
            except Exception:
                pass

        # Fallback 2: bundled default payload
        payload = json.loads(json.dumps(default_payload))  # deep copy
        payload["status"] = "default"
        payload["fetched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(file_path, "w") as f:
                json.dump(payload, f, indent=4)
        except Exception:
            pass
        return payload

    # -- Open-Meteo Flood API (river discharge) ------------------------------
    @classmethod
    def fetch_river_discharge(cls, lat=DEFAULT_LAT, lon=DEFAULT_LON):
        """7-day river discharge series -> data/flood_discharge.json"""
        payload = cls._fetch_and_save(
            OPEN_METEO_FLOOD_URL,
            {"latitude": lat, "longitude": lon,
             "daily": "river_discharge", "timezone": "auto"},
            FLOOD_DISCHARGE_FILE,
            DEFAULT_DISCHARGE,
        )
        # Normalize: attach statistics block (mean/median/max/min/p25/p75)
        daily = payload.get("daily") or {}
        vals = [v for v in (daily.get("river_discharge") or []) if v is not None]
        if vals and not payload.get("statistics"):
            import numpy as np
            arr = np.asarray(vals, dtype=float)
            payload["statistics"] = {
                "mean": round(float(arr.mean()), 2),
                "median": round(float(np.median(arr)), 2),
                "max": round(float(arr.max()), 2),
                "min": round(float(arr.min()), 2),
                "p25": round(float(np.percentile(arr, 25)), 2),
                "p75": round(float(np.percentile(arr, 75)), 2),
            }
        if not payload.get("current_risk"):
            payload["current_risk"] = _risk_from_discharge(vals[-1]) if vals else "LOW"
        return payload

    # -- IMD APIs ------------------------------------------------------------
    @classmethod
    def fetch_imd_basin_qpf(cls):
        """Basin QPF + district/state rainfall -> data/flood_qpf.json"""
        district = cls._fetch_and_save(IMD_DISTRICT_RAINFALL_URL,
                                       DEFAULT_PARAMS["district"],
                                       FLOOD_QPF_FILE + ".district.json",
                                       DEFAULT_QPF["district_rainfall"])
        state = cls._fetch_and_save(IMD_STATE_RAINFALL_URL,
                                    DEFAULT_PARAMS["state"],
                                    FLOOD_QPF_FILE + ".state.json",
                                    DEFAULT_QPF["state_rainfall"])
        basin = cls._fetch_and_save(IMD_BASIN_QPF_URL,
                                    DEFAULT_PARAMS["state"],
                                    FLOOD_QPF_FILE + ".basin.json",
                                    DEFAULT_QPF["basin_qpf"])
        combined = json.loads(json.dumps(DEFAULT_QPF))
        combined.update({
            "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "district_rainfall": district if isinstance(district, dict) else combined["district_rainfall"],
            "state_rainfall": state if isinstance(state, dict) else combined["state_rainfall"],
            "basin_qpf": basin if isinstance(basin, dict) else combined["basin_qpf"],
        })
        with open(FLOOD_QPF_FILE, "w") as f:
            json.dump(combined, f, indent=4)
        return combined

    # -- Google Flood Forecasting API ----------------------------------------
    @classmethod
    def fetch_google_flood(cls):
        """Gauge statuses + flash-flood search; degrades to defaults quietly."""
        gauges = flash = None
        try:
            r = requests.get(f"{GOOGLE_FLOOD_BASE}/floodStatus:queryLatestFloodStatusByGaugeIds",
                             params={"gaugeIds": "hybasin_31013,hybasin_31027"},
                             timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
            if r.status_code == 200:
                gauges = r.json().get("gauges")
        except requests.RequestException as exc:
            print(f"[FloodData] Google gauge status unavailable ({exc}).")
        try:
            r = requests.get(f"{GOOGLE_FLOOD_BASE}/flashFloods:search",
                             params={"lat": DEFAULT_LAT, "lon": DEFAULT_LON},
                             timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
            if r.status_code == 200:
                flash = r.json().get("flashFloods")
        except requests.RequestException as exc:
            print(f"[FloodData] Google flash-flood search unavailable ({exc}).")

        fallback = json.loads(json.dumps(DEFAULT_QPF))
        out = {
            "gauges": gauges or fallback["gauges"],
            "flash_floods": flash or fallback["flash_floods"],
            "source": "google" if (gauges or flash) else "default",
            "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return out

    # -- Combined payload for /api/disaster-data/flood ------------------------
    @classmethod
    def fetch_all_flood_data(cls):
        """Combined IMD + Open-Meteo + Google flood payload."""
        discharge = cls.fetch_river_discharge()
        qpf = cls.fetch_imd_basin_qpf()
        google = cls.fetch_google_flood()

        stats = discharge.get("statistics") or {}
        districts = (qpf.get("district_rainfall") or {}).get("districts", [])
        basin = qpf.get("basin_qpf") or {}
        sub_basins = basin.get("sub_basins", [])
        gauges = google.get("gauges", [])

        reservoir_alerts = sum(1 for g in gauges
                               if str(g.get("status", "")).upper() in ("ABOVE_NORMAL", "HIGH", "SEVERE"))
        heavy_districts = sum(1 for d in districts
                              if float(d.get("rainfall_mm") or 0) >= 64.5)

        return {
            "status": "success",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "discharge": discharge,
            "imd_qpf": qpf,
            "google_flood": google,
            "summary": {
                "mean_discharge_m3s": stats.get("mean"),
                "max_discharge_m3s": stats.get("max"),
                "current_risk": discharge.get("current_risk", "LOW"),
                "sub_basins_qpf": len(sub_basins),
                "high_risk_sub_basins": sum(1 for sb in sub_basins
                                            if str(sb.get("risk", "")).upper() == "HIGH"),
                "heavy_rainfall_districts": heavy_districts,
                "reservoir_alerts": reservoir_alerts,
                "gauges_reporting": len(gauges),
                "flash_flood_zones": len(google.get("flash_floods", [])),
            },
        }
