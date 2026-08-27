"""
Wind Preparedness Unit — IMD Wind API Fetchers
==============================================
Fetches live data from 2 IMD APIs and persists each response to /data:

    wind_warnings.json  -> /api/v1/districtwarning  (wind hazard codes)
    wind_nowcast.json   -> /api/v1/stationnowcast   (gust categories)

Wind-relevant IMD district warning codes:
    4  -> Thunderstorm & Lightning, Squall
    7  -> Dust Raising Winds
    8  -> Strong Surface Winds
    14 -> Severe Thunderstorms (62-87 kmph gusts)
    15 -> Very Severe Thunderstorms (>87 kmph gusts)
    32 -> Severe Dust Storm

Station nowcast wind categories:
    Cat4  -> Light Thunderstorms (<40 kmph gusts)
    Cat9  -> Moderate Thunderstorms (41-61 kmph gusts)
    Cat14 -> Severe Thunderstorms (62-87 kmph gusts)
    Cat15 -> Very Severe Thunderstorms (>87 kmph gusts)
    Cat18 -> Severe Dust Storm (>61 kmph gusts, visibility <200 m)

Every fetcher degrades gracefully: live IMD API -> cached file -> bundled
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
WIND_WARNINGS_FILE = os.path.join(DATA_DIR, "wind_warnings.json")
WIND_NOWCAST_FILE = os.path.join(DATA_DIR, "wind_nowcast.json")

# ---------------------------------------------------------------------------
# IMD API endpoints
# ---------------------------------------------------------------------------
IMD_DISTRICT_WARNING_URL = "https://api.imd.gov.in/api/v1/districtwarning"
IMD_STATION_NOWCAST_URL = "https://api.imd.gov.in/api/v1/stationnowcast"

# Default query ids (Andhra Pradesh warnings, Guntur station)
DEFAULT_PARAMS = {
    "warning": {"id": "573"},
    "nowcast": {"id": "Guntur"},
}

REQUEST_TIMEOUT = 10

# IMD color codes for warning severity
WARNING_COLORS = {
    "Red": "#FF0000",
    "Orange": "#FFA500",
    "Yellow": "#FFFF00",
    "Green": "#7cfc00",
}

# Wind-relevant district warning codes -> labels + gust ranges
WIND_WARNING_CODES = {
    4: {"label": "Thunderstorm & Lightning, Squall", "gust_range_kmph": "40-60"},
    7: {"label": "Dust Raising Winds", "gust_range_kmph": "25-40"},
    8: {"label": "Strong Surface Winds", "gust_range_kmph": "40-50"},
    14: {"label": "Severe Thunderstorms", "gust_range_kmph": "62-87"},
    15: {"label": "Very Severe Thunderstorms", "gust_range_kmph": ">87"},
    32: {"label": "Severe Dust Storm", "gust_range_kmph": ">61 (vis <200 m)"},
}

# Station nowcast wind categories -> labels + gust ranges
NOWCAST_WIND_CATEGORIES = {
    "Cat4": {"label": "Light Thunderstorms", "gust_range_kmph": "<40"},
    "Cat9": {"label": "Moderate Thunderstorms", "gust_range_kmph": "41-61"},
    "Cat14": {"label": "Severe Thunderstorms", "gust_range_kmph": "62-87"},
    "Cat15": {"label": "Very Severe Thunderstorms", "gust_range_kmph": ">87"},
    "Cat18": {"label": "Severe Dust Storm", "gust_range_kmph": ">61 (vis <200 m)"},
}

# ---------------------------------------------------------------------------
# Default fallback payloads (used when IMD API is unreachable and no cache)
# ---------------------------------------------------------------------------
DEFAULT_WIND_WARNINGS = {
    "status": "default",
    "warnings_count": 3,
    "warnings": [
        {"district": "Guntur", "warning_code": 15,
         "warning_label": "Very Severe Thunderstorms",
         "warning_level": "Red Warning", "color": "#FF0000",
         "gust_range_kmph": ">87",
         "message": "Very severe thunderstorm with gusts exceeding 87 kmph; uprooting of trees and power line damage likely.",
         "valid_from": "today", "valid_to": "+24h",
         "polygon": [[16.28, 80.40], [16.34, 80.48], [16.31, 80.52], [16.24, 80.44]]},
        {"district": "Bapatla", "warning_code": 14,
         "warning_label": "Severe Thunderstorms",
         "warning_level": "Orange Warning", "color": "#FFA500",
         "gust_range_kmph": "62-87",
         "message": "Severe thunderstorm gusts 62-87 kmph; secure hoardings and loose roof sheets.",
         "valid_from": "today", "valid_to": "+24h",
         "polygon": [[15.88, 80.42], [15.94, 80.50], [15.90, 80.55], [15.83, 80.47]]},
        {"district": "Palnadu", "warning_code": 8,
         "warning_label": "Strong Surface Winds",
         "warning_level": "Yellow Warning", "color": "#FFFF00",
         "gust_range_kmph": "40-50",
         "message": "Strong surface winds 40-50 kmph; dust raising possible on highways.",
         "valid_from": "today", "valid_to": "+24h",
         "polygon": [[16.10, 79.82], [16.20, 79.95], [16.12, 80.02], [16.02, 79.90]]},
        {"district": "Prakasam", "warning_code": 32,
         "warning_label": "Severe Dust Storm",
         "warning_level": "Orange Warning", "color": "#FFA500",
         "gust_range_kmph": ">61 (vis <200 m)",
         "message": "Severe dust storm; visibility below 200 m on NH-16 corridor. Drive with headlights on.",
         "valid_from": "today", "valid_to": "+12h",
         "polygon": [[15.55, 79.40], [15.65, 79.55], [15.58, 79.65], [15.48, 79.52]]},
    ],
}

DEFAULT_WIND_NOWCAST = {
    "status": "default",
    "station": "Guntur",
    "issued_at": None,  # filled at runtime
    "alerts_count": 2,
    "nowcast": [
        {"time": "+1h", "category": "Cat9", "category_label": "Moderate Thunderstorms",
         "gust_speed_kmph": 48, "alert": False},
        {"time": "+2h", "category": "Cat14", "category_label": "Severe Thunderstorms",
         "gust_speed_kmph": 71, "alert": True,
         "message": "Severe gusts expected — secure loose objects, avoid trees and power lines."},
        {"time": "+3h", "category": "Cat15", "category_label": "Very Severe Thunderstorms",
         "gust_speed_kmph": 92, "alert": True,
         "message": "Very severe gusts >87 kmph — stay indoors, away from windows."},
        {"time": "+4h", "category": "Cat9", "category_label": "Moderate Thunderstorms",
         "gust_speed_kmph": 52, "alert": False},
        {"time": "+5h", "category": "Cat4", "category_label": "Light Thunderstorms",
         "gust_speed_kmph": 32, "alert": False},
        {"time": "+6h", "category": "Cat4", "category_label": "Light Thunderstorms",
         "gust_speed_kmph": 25, "alert": False},
    ],
}


class WindDataManager:
    """Fetches IMD wind APIs, caches to /data, falls back gracefully."""

    @staticmethod
    def _fetch_and_save(url, params, file_path, default_payload):
        """Generic fetch->save->fallback pipeline shared by both APIs."""
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT,
                                headers={"Accept": "application/json",
                                         "User-Agent": "GMC-WindPreparedness/1.0"})
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
            print(f"[WindData] {url} unreachable ({exc}); using cached/default data.")

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

    @classmethod
    def fetch_district_warnings(cls):
        """District wind warnings (codes 4/7/8/14/15/32) -> data/wind_warnings.json"""
        return cls._fetch_and_save(IMD_DISTRICT_WARNING_URL,
                                   DEFAULT_PARAMS["warning"],
                                   WIND_WARNINGS_FILE,
                                   DEFAULT_WIND_WARNINGS)

    @classmethod
    def fetch_station_nowcast(cls):
        """Station gust nowcast (Cat4/9/14/15/18) -> data/wind_nowcast.json"""
        payload = cls._fetch_and_save(IMD_STATION_NOWCAST_URL,
                                      DEFAULT_PARAMS["nowcast"],
                                      WIND_NOWCAST_FILE,
                                      DEFAULT_WIND_NOWCAST)
        if isinstance(payload, dict) and not payload.get("issued_at"):
            payload["issued_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return payload

    @classmethod
    def fetch_all_wind_data(cls):
        """Fetch both IMD wind APIs and return a combined payload."""
        warnings = cls.fetch_district_warnings()
        nowcast = cls.fetch_station_nowcast()

        warning_list = warnings.get("warnings", []) if isinstance(warnings, dict) else []
        nowcast_list = nowcast.get("nowcast", []) if isinstance(nowcast, dict) else []
        gusts = [n.get("gust_speed_kmph", 0) for n in nowcast_list if isinstance(n, dict)]

        combined = {
            "status": "success",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "district_warnings": warnings,
            "station_nowcast": nowcast,
            "summary": {
                "active_warnings": len(warning_list),
                "red_warnings": sum(1 for w in warning_list if "red" in str(w.get("warning_level", "")).lower()),
                "orange_warnings": sum(1 for w in warning_list if "orange" in str(w.get("warning_level", "")).lower()),
                "yellow_warnings": sum(1 for w in warning_list if "yellow" in str(w.get("warning_level", "")).lower()),
                "green_warnings": sum(1 for w in warning_list if "green" in str(w.get("warning_level", "")).lower()),
                "hazard_districts": len({w.get("district") for w in warning_list}),
                "nowcast_alerts": sum(1 for n in nowcast_list if n.get("alert")),
                "max_gust_kmph": max(gusts) if gusts else 0,
                "stations_reporting": 1,
            },
        }
        return combined
