"""QA route verification for the Landslide Early Warning Unit."""
import json

from app import create_app

app = create_app()
client = app.test_client()

checks = [
    ("GET", "/disasters/landslides"),
    ("GET", "/api/disaster-data/landslide"),
    ("GET", "/api/predict/landslide"),
    ("POST", "/api/disaster-data/landslide/refresh"),
]

all_ok = True
for method, url in checks:
    resp = client.open(url, method=method)
    ok = resp.status_code == 200
    all_ok = all_ok and ok
    print(f"[{resp.status_code}] {method} {url}")
    if not ok:
        body = resp.get_data(as_text=True)[:500]
        print("   body:", body)
    elif url.startswith("/api/predict"):
        data = json.loads(resp.get_data(as_text=True))
        print("   risk:", data.get("current_risk"),
              "| confidence:", data.get("risk_confidence_pct"),
              "| surface pts:", len(data.get("risk_surface", [])))
    elif url.endswith("/refresh"):
        data = json.loads(resp.get_data(as_text=True))
        print("   status:", data.get("status"),
              "| classifier:", data.get("classifier"),
              "| fallback:", data.get("fallback_model"))
    elif url == "/api/disaster-data/landslide":
        data = json.loads(resp.get_data(as_text=True))
        print("   summary keys:", sorted((data.get("summary") or {}).keys())[:6], "...")

print("ALL_ROUTES_OK" if all_ok else "ROUTE_FAILURES_DETECTED")