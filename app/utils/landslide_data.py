"""
Landslide Early Warning Unit — IMD + USGS + NOAA/NCEI + DEM Terrain Fetchers
============================================================================
Fetches live inputs from 4 source families and persists each response to /data:

    landslide_imd.json     -> IMD district/state rainfall + basin QPF
    landslide_seismic.json -> USGS Earthquake Catalog (seismic triggers)
    landslide_soil.json    -> NOAA/NCEI climate data (soil-moisture proxy +
                              precipitation history)
    landslide_terrain.json -> DEM raster extraction (slope / elevation)
    landslide_inputs.json  -> combined payload served to the UI + ML pipeline

APIs
----
IMD (India Meteorological Department):
    /api/v1/districtrainfall -> district rainfall (landslide driver)
    /api/v1/staterainfall    -> state rainfall aggregate
    /api/v1/basinqpf         -> river basin Quantitative Precipitation Forecast

USGS Earthquake Catalog (FDSN event service):
    https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson
    Magnitude >= 2.5 events within 500 km of Guntur over the trailing 30 days
    are used as seismic slope-failure triggers.

NOAA NCEI Access Data Service v1:
    https://www.ncei.noaa.gov/access/services/data/v1
    dataset=global-summary-of-the-day -> daily precipitation history used to
    derive an Antecedent Precipitation Index (API) soil-moisture proxy.

DEM terrain:
    Bundled GeoTIFF rasters (data/dem/*.tif) are read via rasterio when the
    library and files are available; slope/elevation statistics and hazard
    zones are extracted from the raster grid. Otherwise the unit degrades to
    the cached terrain snapshot, then to a bundled default terrain model.

Every fetcher degrades gracefully: live API -> cached file -> bundled default
payload, so the UI, ML pipeline and scheduler never crash.
"""

import os
import json
import glob
import datetime
import time
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# File paths (saved outputs)
# ---------------------------------------------------------------------------
LANDSLIDE_INPUTS_FILE = os.path.join(DATA_DIR, "landslide_inputs.json")
LANDSLIDE_IMD_FILE = os.path.join(DATA_DIR, "landslide_imd.json")
LANDSLIDE_SEISMIC_FILE = os.path.join(DATA_DIR, "landslide_seismic.json")
LANDSLIDE_SOIL_FILE = os.path.join(DATA_DIR, "landslide_soil.json")
LANDSLIDE_TERRAIN_FILE = os.path.join(DATA_DIR, "landslide_terrain.json")

# Bundled DEM raster candidates (searched in order)
DEM_RASTER_PATTERNS = [
    os.path.join(DATA_DIR, "dem", "*.tif"),
    os.path.join(DATA_DIR, "dem", "*.tiff"),
    os.path.join(DATA_DIR, "guntur_dem.tif"),
]

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
IMD_DISTRICT_RAINFALL_URL = "https://api.imd.gov.in/api/v1/districtrainfall"
IMD_STATE_RAINFALL_URL = "https://api.imd.gov.in/api/v1/staterainfall"
IMD_BASIN_QPF_URL = "https://api.imd.gov.in/api/v1/basinqpf"

USGS_EARTHQUAKE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
NCEI_DATA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"

REQUEST_TIMEOUT = 10

# In-process TTL cache for the combined payload so UI polling and the ML
# pipeline never re-hit the upstream APIs on every request. Scheduler jobs
# and the manual-refresh endpoint bypass it via force_refresh=True.
COMBINED_CACHE_TTL_SECONDS = 300
_COMBINED_CACHE = {"payload": None, "ts": 0.0}

# Guntur, Andhra Pradesh — hilly terrain on the Krishna delta margin
DEFAULT_LAT, DEFAULT_LON = 16.3067, 80.4365

# NCEI GSOD station: Vijayawada / Gannavaram Airport (nearest long-record
# station to Guntur); degrades to bundled defaults when unreachable.
NCEI_STATION_ID = "43195099999"

DEFAULT_PARAMS = {
    "district": {"id": "573"},
    "state": {"id": "andhra"},
}

REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "GMC-LandslideEarlyWarning/1.0",
}

# ---------------------------------------------------------------------------
# Default fallback payloads (used when APIs are unreachable and no cache)
# ---------------------------------------------------------------------------
DEFAULT_IMD = {
    "status": "default",
    "basin_qpf": {
        "basin_name": "Krishna Basin (Lower)",
        "issued_at": None,
        "polygon": [[16.05, 80.10], [16.35, 80.30], [16.20, 80.65], [15.90, 80.40]],
        "sub_basins": [
            {"name": "Hills Sub-basin (NE Guntur)", "qpf_mm": 88.6, "risk": "HIGH"},
            {"name": "Krishna Delta Margin", "qpf_mm": 54.2, "risk": "MODERATE"},
            {"name": "Nagarjuna Sagar Foothills", "qpf_mm": 71.8, "risk": "HIGH"},
        ],
    },
    "district_rainfall": {
        "districts": [
            {"district": "Guntur", "rainfall_mm": 96.4, "normal_mm": 48.2,
             "departure_percent": 100.0, "category": "Very Heavy",
             "lat": 16.3067, "lon": 80.4365},
            {"district": "Palnadu", "rainfall_mm": 112.8, "normal_mm": 52.6,
             "departure_percent": 114.4, "category": "Very Heavy",
             "lat": 16.1067, "lon": 79.9365},
            {"district": "Bapatla", "rainfall_mm": 48.2, "normal_mm": 44.0,
             "departure_percent": 9.5, "category": "Moderate",
             "lat": 15.9049, "lon": 80.4675},
            {"district": "NTR (Vijayawada)", "rainfall_mm": 84.6, "normal_mm": 50.1,
             "departure_percent": 68.9, "category": "Heavy",
             "lat": 16.5062, "lon": 80.6480},
        ],
    },
    "state_rainfall": {
        "state": "Andhra Pradesh",
        "actual_mm": 68.4, "normal_mm": 47.8, "departure_percent": 43.1,
    },
}

DEFAULT_SEISMIC = {
    "status": "default",
    "source": "USGS Earthquake Catalog (bundled snapshot)",
    "window_days": 30,
    "events": [
        {"mag": 4.2, "place": "Andhra Pradesh — Karnataka border region",
         "time": (datetime.datetime.now() - datetime.timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"),
         "lat": 15.812, "lon": 79.221, "depth_km": 10.0},
        {"mag": 3.1, "place": "Near Ongole, Andhra Pradesh",
         "time": (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
         "lat": 15.503, "lon": 80.047, "depth_km": 12.0},
    ],
    "trigger_score": 0.7,
}

DEFAULT_SOIL = {
    "status": "default",
    "source": "NOAA NCEI (bundled snapshot)",
    "station_id": NCEI_STATION_ID,
    "station_name": "VIJAYAWADA/GANNAVARAM (IN)",
    "soil_moisture_frac": 0.68,
    "antecedent_precip_index_mm": 102.4,
    "saturation_pct": 68.0,
    "history": [
        {"date": (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
         "precip_mm": round(18.0 + (i % 5) * 6.5, 1),
         "api_index_mm": round(70.0 + (28 - i) * 1.15, 1)}
        for i in range(29, -1, -1)
    ],
}

DEFAULT_TERRAIN = {
    "status": "default",
    "source": "bundled-default-dem",
    "crs": "EPSG:4326",
    "resolution_m": 30,
    "extent": {"min_lat": 15.80, "max_lat": 16.60, "min_lon": 79.90, "max_lon": 80.90},
    "mean_elevation_m": 88.0,
    "max_elevation_m": 438.0,
    "mean_slope_deg": 12.6,
    "max_slope_deg": 46.0,
    "zones": [
        {"name": "Kotappakonda Hill Slopes", "slope_deg": 42.0, "elevation_m": 438.0,
         "risk": "EXTREME", "stability": "unstable",
         "polygon": [[16.196, 79.982], [16.240, 80.022], [16.212, 80.062], [16.168, 80.014]]},
        {"name": "Nagarjuna Sagar Foothills", "slope_deg": 34.5, "elevation_m": 182.0,
         "risk": "HIGH", "stability": "marginally stable",
         "polygon": [[16.420, 79.920], [16.465, 79.958], [16.438, 80.004], [16.392, 79.962]]},
        {"name": "Palnadu Escarpment", "slope_deg": 31.2, "elevation_m": 156.0,
         "risk": "HIGH", "stability": "marginally stable",
         "polygon": [[16.052, 79.862], [16.098, 79.900], [16.072, 79.948], [16.026, 79.906]]},
        {"name": "Guntur Urban Periphery Cut Slopes", "slope_deg": 22.8, "elevation_m": 61.0,
         "risk": "MODERATE", "stability": "stable (engineered)",
         "polygon": [[16.280, 80.400], [16.330, 80.440], [16.305, 80.492], [16.255, 80.450]]},
        {"name": "Krishna Delta Flatlands", "slope_deg": 4.2, "elevation_m": 12.0,
         "risk": "LOW", "stability": "stable",
         "polygon": [[16.140, 80.520], [16.205, 80.566], [16.178, 80.640], [16.112, 80.592]]},
    ],
}

# ---------------------------------------------------------------------------
# Landslide-risk thresholds
# ---------------------------------------------------------------------------
RAINFALL_HEAVY_MM = 64.5      # IMD "heavy" daily rainfall — slide watch
RAINFALL_VERY_HEAVY_MM = 115.6  # IMD "very heavy" — slide warning
SOIL_SATURATION_ALERT_FRAC = 0.60   # soil-moisture fraction alert level
SEISMIC_TRIGGER_MAG = 4.0     # M>=4 within range counts as a trigger
SEISMIC_RADIUS_KM = 500       # USGS search radius
SEISMIC_WINDOW_DAYS = 30      # trailing window for seismic triggers

LANDSLIDE_RISK_COLORS = {"LOW": "#2e7d32", "MODERATE": "#fbc02d",
                         "HIGH": "#FFA500", "EXTREME": "#FF0000"}


def hazard_from_inputs(rainfall_mm, slope_deg, soil_moisture_frac, seismic_score):
    """Transparent rule-based landslide hazard classifier.

    Weighted blend of the four core drivers (rainfall intensity, slope,
    soil moisture, seismic triggers) mapped to LOW/MODERATE/HIGH/EXTREME.
    Used to label ML training samples and to sanity-check predictions.
    """
    rain_n = min(max(rainfall_mm, 0.0) / 120.0, 1.5)          # 120 mm/day ~ trigger
    slope_n = min(max((slope_deg - 10.0) / 35.0, 0.0), 1.5)   # 10° flat .. 45° critical
    soil_n = min(max(soil_moisture_frac, 0.0) / 0.75, 1.5)    # 0.75 ~ saturation
    seis_n = min(max(seismic_score, 0.0) / 3.0, 1.5)          # ~3 weighted M>=4 events
    score = 0.40 * rain_n + 0.25 * slope_n + 0.22 * soil_n + 0.13 * seis_n
    if score >= 0.78:
        return "EXTREME"
    if score >= 0.55:
        return "HIGH"
    if score >= 0.32:
        return "MODERATE"
    return "LOW"


class LandslideDataManager:
    """Fetches IMD + USGS + NOAA/NCEI + DEM inputs, caches to /data."""

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
            print(f"[LandslideData] {url} unreachable ({exc}); using cached/default data.")

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

    # -- IMD Rainfall APIs ---------------------------------------------------
    @classmethod
    def fetch_imd_rainfall(cls):
        """District/state rainfall + basin QPF -> data/landslide_imd.json"""
        district = cls._fetch_and_save(IMD_DISTRICT_RAINFALL_URL,
                                       DEFAULT_PARAMS["district"],
                                       LANDSLIDE_IMD_FILE + ".district.json",
                                       DEFAULT_IMD["district_rainfall"])
        state = cls._fetch_and_save(IMD_STATE_RAINFALL_URL,
                                    DEFAULT_PARAMS["state"],
                                    LANDSLIDE_IMD_FILE + ".state.json",
                                    DEFAULT_IMD["state_rainfall"])
        basin = cls._fetch_and_save(IMD_BASIN_QPF_URL,
                                    DEFAULT_PARAMS["state"],
                                    LANDSLIDE_IMD_FILE + ".basin.json",
                                    DEFAULT_IMD["basin_qpf"])
        combined = json.loads(json.dumps(DEFAULT_IMD))
        combined.update({
            "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "district_rainfall": district if isinstance(district, dict) else combined["district_rainfall"],
            "state_rainfall": state if isinstance(state, dict) else combined["state_rainfall"],
            "basin_qpf": basin if isinstance(basin, dict) else combined["basin_qpf"],
        })
        with open(LANDSLIDE_IMD_FILE, "w") as f:
            json.dump(combined, f, indent=4)
        return combined

    # -- USGS Earthquake Catalog API ------------------------------------------
    @classmethod
    def fetch_seismic_triggers(cls):
        """M>=2.5 quakes within 500 km / 30 days -> data/landslide_seismic.json"""
        start = (datetime.datetime.utcnow() -
                 datetime.timedelta(days=SEISMIC_WINDOW_DAYS)).strftime("%Y-%m-%d")
        params = {
            "format": "geojson",
            "starttime": start,
            "latitude": DEFAULT_LAT,
            "longitude": DEFAULT_LON,
            "maxradiuskm": SEISMIC_RADIUS_KM,
            "minmagnitude": 2.5,
            "orderby": "time",
            "limit": 200,
        }
        raw = cls._fetch_and_save(USGS_EARTHQUAKE_URL, params,
                                  LANDSLIDE_SEISMIC_FILE, DEFAULT_SEISMIC)

        # Normalize: accept either a fresh geojson response or the cached/
        # default snapshot shape ({"events": [...]})
        events = []
        if isinstance(raw, dict) and isinstance(raw.get("features"), list):
            for feat in raw["features"]:
                try:
                    props = feat.get("properties") or {}
                    geom = feat.get("geometry") or {}
                    coords = (geom.get("coordinates") or [None, None, None])
                    events.append({
                        "mag": props.get("mag"),
                        "place": props.get("place"),
                        "time": datetime.datetime.utcfromtimestamp(
                            (props.get("time") or 0) / 1000.0
                        ).strftime("%Y-%m-%d %H:%M:%S") if props.get("time") else None,
                        "lat": coords[1],
                        "lon": coords[0],
                        "depth_km": coords[2],
                    })
                except Exception:
                    continue
        elif isinstance(raw, dict) and isinstance(raw.get("events"), list):
            events = raw["events"]

        trigger_score = round(sum(
            max(0.0, float(e.get("mag") or 0) - (SEISMIC_TRIGGER_MAG - 0.5))
            for e in events if float(e.get("mag") or 0) >= SEISMIC_TRIGGER_MAG
        ), 2)

        out = {
            "status": "success" if events else "default",
            "source": "USGS Earthquake Catalog (FDSN)",
            "window_days": SEISMIC_WINDOW_DAYS,
            "radius_km": SEISMIC_RADIUS_KM,
            "events": events[:100],
            "event_count": len(events),
            "max_magnitude": max([float(e.get("mag") or 0) for e in events], default=0.0),
            "trigger_score": trigger_score,
            "trigger_active": trigger_score >= 0.5,
            "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(LANDSLIDE_SEISMIC_FILE, "w") as f:
            json.dump(out, f, indent=4)
        return out

    # -- NOAA/NCEI soil & climate data ----------------------------------------
    @classmethod
    def fetch_soil_climate(cls):
        """NCEI daily precipitation -> API soil-moisture proxy ->
        data/landslide_soil.json"""
        end = datetime.date.today()
        start = end - datetime.timedelta(days=45)
        params = {
            "dataset": "global-summary-of-the-day",
            "stations": NCEI_STATION_ID,
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
            "format": "json",
            "limit": 60,
        }
        raw = cls._fetch_and_save(NCEI_DATA_URL, params,
                                  LANDSLIDE_SOIL_FILE, DEFAULT_SOIL)

        rows = []
        if isinstance(raw, list):
            rows = raw
        elif isinstance(raw, dict) and isinstance(raw.get("history"), list):
            # Cached/default snapshot shape — recompute nothing, just enrich
            snap = json.loads(json.dumps(raw))
            snap.setdefault("source", "NOAA NCEI (cached)")
            snap["saturation_pct"] = round(
                float(snap.get("soil_moisture_frac", 0.0)) * 100, 1)
            with open(LANDSLIDE_SOIL_FILE, "w") as f:
                json.dump(snap, f, indent=4)
            return snap

        # Parse NCEI GSOD rows -> daily precipitation (inches -> mm)
        parsed = []
        for row in rows:
            try:
                date = str(row.get("DATE") or "")[:10]
                prcp_in = row.get("PRCP")
                if not date or prcp_in in (None, "", 99.99):
                    continue
                parsed.append({"date": date, "precip_mm": round(float(prcp_in) * 25.4, 1)})
            except Exception:
                continue
        parsed.sort(key=lambda r: r["date"])

        if parsed:
            # Antecedent Precipitation Index (recursive, k=0.85) as the
            # soil-moisture proxy; normalised against a 150 mm reference.
            api_mm = 0.0
            for r in parsed:
                api_mm = 0.85 * api_mm + r["precip_mm"]
                r["api_index_mm"] = round(api_mm, 1)
            soil_frac = round(min(api_mm / 150.0, 1.0), 3)
            out = {
                "status": "success",
                "source": "NOAA NCEI Access Data Service v1 (GSOD)",
                "station_id": str(rows[0].get("STATION") or NCEI_STATION_ID),
                "station_name": str(rows[0].get("NAME") or "Unknown station"),
                "soil_moisture_frac": soil_frac,
                "antecedent_precip_index_mm": round(api_mm, 1),
                "saturation_pct": round(soil_frac * 100, 1),
                "history": parsed[-30:],
                "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            out = json.loads(json.dumps(DEFAULT_SOIL))
            out["status"] = "default"
            out["fetched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(LANDSLIDE_SOIL_FILE, "w") as f:
            json.dump(out, f, indent=4)
        return out

    # -- DEM terrain (bundled raster files) ------------------------------------
    @classmethod
    def _find_dem_raster(cls):
        for pattern in DEM_RASTER_PATTERNS:
            matches = sorted(glob.glob(pattern))
            if matches:
                return matches[0]
        return None

    @classmethod
    def _read_dem_raster(cls, raster_path):
        """Extract slope/elevation stats + hazard zones from a DEM GeoTIFF."""
        import numpy as np
        import rasterio  # optional dependency

        with rasterio.open(raster_path) as ds:
            dem = ds.read(1, masked=True).astype(float)
            transform = ds.transform
            crs = ds.crs

        filled = np.nan_to_num(np.ma.filled(dem, np.nan),
                               nan=float(np.nanmean(np.ma.filled(dem, np.nan)) or 0.0))
        gy, gx = np.gradient(filled)
        # metres per degree latitude ~111,320; assume geographic CRS
        geographic = crs is None or (getattr(crs, "is_geographic", True))
        mx = 111320.0 if geographic else abs(transform.a)
        my = 111320.0 if geographic else abs(transform.e)
        slope = np.degrees(np.arctan(np.sqrt((gx * mx) ** 2 + (gy * my) ** 2)))

        # Coarse 20x20 grid -> per-cell means -> steepest cells become zones
        ny, nx = 20, 20
        h, w = slope.shape
        cell_slopes, cell_elevs, centers = [], [], []
        for i in range(ny):
            for j in range(nx):
                block_s = slope[i * h // ny:(i + 1) * h // ny,
                                j * w // nx:(j + 1) * w // nx]
                block_e = filled[i * h // ny:(i + 1) * h // ny,
                                 j * w // nx:(j + 1) * w // nx]
                cell_slopes.append(float(block_s.mean()))
                cell_elevs.append(float(block_e.mean()))
                x, y = transform * ((j + 0.5) * w / nx, (i + 0.5) * h / ny)
                centers.append((float(x), float(y)))

        order = sorted(range(len(cell_slopes)),
                       key=lambda k: cell_slopes[k], reverse=True)[:6]
        half = 0.03  # ~3 km square polygon per zone
        zones = []
        for rank, k in enumerate(order):
            s = cell_slopes[k]
            lon, lat = centers[k]
            risk = ("EXTREME" if s >= 40 else "HIGH" if s >= 30
                    else "MODERATE" if s >= 15 else "LOW")
            zones.append({
                "name": f"DEM Steep Zone #{rank + 1}",
                "slope_deg": round(s, 1),
                "elevation_m": round(cell_elevs[k], 1),
                "risk": risk,
                "stability": "unstable" if s >= 30 else "marginally stable",
                "polygon": [[lat - half, lon - half], [lat - half, lon + half],
                            [lat + half, lon + half], [lat + half, lon - half]],
            })

        out = {
            "status": "success",
            "source": f"bundled DEM raster: {os.path.basename(raster_path)}",
            "crs": str(crs) if crs else "unknown",
            "resolution_m": round(abs(transform.a) * (111320.0 if geographic else 1.0), 1),
            "mean_elevation_m": round(float(filled.mean()), 1),
            "max_elevation_m": round(float(filled.max()), 1),
            "mean_slope_deg": round(float(slope.mean()), 1),
            "max_slope_deg": round(float(slope.max()), 1),
            "zones": zones,
            "extracted_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return out

    @classmethod
    def load_dem_terrain(cls):
        """DEM terrain loader: bundled raster -> cached JSON -> bundled default."""
        raster_path = cls._find_dem_raster()
        if raster_path:
            try:
                out = cls._read_dem_raster(raster_path)
                with open(LANDSLIDE_TERRAIN_FILE, "w") as f:
                    json.dump(out, f, indent=4)
                return out
            except Exception as exc:
                print(f"[LandslideData] DEM raster unavailable ({exc}); "
                      f"using cached/default terrain.")

        # Fallback 1: cached terrain snapshot
        if os.path.exists(LANDSLIDE_TERRAIN_FILE):
            try:
                with open(LANDSLIDE_TERRAIN_FILE, "r") as f:
                    cached = json.load(f)
                if isinstance(cached, dict) and cached.get("status") != "default":
                    return cached
            except Exception:
                pass

        # Fallback 2: bundled default terrain model
        payload = json.loads(json.dumps(DEFAULT_TERRAIN))
        payload["fetched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(LANDSLIDE_TERRAIN_FILE, "w") as f:
                json.dump(payload, f, indent=4)
        except Exception:
            pass
        return payload

    # -- Cached snapshot (zero network) -----------------------------------------
    @classmethod
    def get_cached_inputs(cls):
        """Return the last persisted /data/landslide_inputs.json without any
        network I/O. Used by the ML trainer so model (re)building never blocks
        on upstream APIs."""
        try:
            with open(LANDSLIDE_INPUTS_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("summary"):
                return data
        except Exception:
            pass
        return None

    # -- Combined payload for /api/disaster-data/landslide ---------------------
    @classmethod
    def fetch_all_landslide_data(cls, force_refresh=False):
        """Combined rainfall + seismic + soil + terrain payload, persisted to
        data/landslide_inputs.json.

        Memoised in-process for COMBINED_CACHE_TTL_SECONDS; pass
        force_refresh=True (manual refresh endpoint / scheduler) to bypass.
        """
        now = time.time()
        if (not force_refresh
                and _COMBINED_CACHE["payload"] is not None
                and now - _COMBINED_CACHE["ts"] < COMBINED_CACHE_TTL_SECONDS):
            return _COMBINED_CACHE["payload"]

        imd = cls.fetch_imd_rainfall()
        seismic = cls.fetch_seismic_triggers()
        soil = cls.fetch_soil_climate()
        terrain = cls.load_dem_terrain()

        districts = (imd.get("district_rainfall") or {}).get("districts", [])
        sub_basins = ((imd.get("basin_qpf") or {}).get("sub_basins")) or []
        zones = terrain.get("zones", [])

        districts_at_risk = [
            d for d in districts
            if float(d.get("rainfall_mm") or 0) >= RAINFALL_HEAVY_MM
            or float(d.get("departure_percent") or 0) >= 60
        ]
        rainfall_exceeded = (
            sum(1 for d in districts
                if float(d.get("rainfall_mm") or 0) >= RAINFALL_HEAVY_MM)
            + sum(1 for sb in sub_basins
                  if float(sb.get("qpf_mm") or 0) >= RAINFALL_HEAVY_MM)
        )
        soil_frac = float(soil.get("soil_moisture_frac") or 0.0)
        max_qpf = max([float(sb.get("qpf_mm") or 0) for sb in sub_basins], default=0.0)
        peak_rain = max([float(d.get("rainfall_mm") or 0) for d in districts],
                        default=0.0)
        driving_rain = max(peak_rain, max_qpf)
        seismic_score = float(seismic.get("trigger_score") or 0.0)
        mean_slope = float(terrain.get("mean_slope_deg") or 0.0)

        current_risk = hazard_from_inputs(
            driving_rain, mean_slope, soil_frac, seismic_score)

        combined = {
            "status": "success",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": {"city": "Guntur", "state": "Andhra Pradesh",
                         "lat": DEFAULT_LAT, "lon": DEFAULT_LON},
            "imd_rainfall": imd,
            "seismic": seismic,
            "soil": soil,
            "terrain": terrain,
            "thresholds": {
                "rainfall_heavy_mm": RAINFALL_HEAVY_MM,
                "rainfall_very_heavy_mm": RAINFALL_VERY_HEAVY_MM,
                "soil_saturation_alert_frac": SOIL_SATURATION_ALERT_FRAC,
                "seismic_trigger_mag": SEISMIC_TRIGGER_MAG,
            },
            "summary": {
                "districts_at_risk": len(districts_at_risk),
                "districts_reporting": len(districts),
                "rainfall_threshold_exceeded": rainfall_exceeded,
                "peak_district_rainfall_mm": round(peak_rain, 1),
                "max_basin_qpf_mm": round(max_qpf, 1),
                "soil_moisture_frac": soil_frac,
                "soil_saturation_pct": round(soil_frac * 100, 1),
                "soil_saturation_alert": soil_frac >= SOIL_SATURATION_ALERT_FRAC,
                "seismic_events_30d": int(seismic.get("event_count") or len(seismic.get("events", []))),
                "max_magnitude_30d": float(seismic.get("max_magnitude") or 0.0),
                "seismic_trigger_active": bool(seismic.get("trigger_active")),
                "mean_slope_deg": round(mean_slope, 1),
                "max_slope_deg": float(terrain.get("max_slope_deg") or 0.0),
                "high_slope_zones": sum(1 for z in zones
                                        if float(z.get("slope_deg") or 0) >= 30),
                "current_risk": current_risk,
            },
        }
        with open(LANDSLIDE_INPUTS_FILE, "w") as f:
            json.dump(combined, f, indent=4)
        _COMBINED_CACHE["payload"] = combined
        _COMBINED_CACHE["ts"] = time.time()
        return combined
