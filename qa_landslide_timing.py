"""Timing verification: landslide endpoints must respond quickly."""
import time

from app import create_app

app = create_app()
client = app.test_client()


def timed(method, url, label):
    t0 = time.time()
    resp = client.open(url, method=method)
    dt = time.time() - t0
    print(f"[{resp.status_code}] {label}: {dt:.2f}s")
    return resp, dt


print("--- cold-ish pass (fresh process; data files already cached on disk) ---")
timed("GET", "/api/disaster-data/landslide", "data  (1st call)")
timed("GET", "/api/predict/landslide", "predict (1st call)")

print("--- warm pass (TTL cache + warm model) ---")
_, d1 = timed("GET", "/api/disaster-data/landslide", "data  (2nd call)")
_, p1 = timed("GET", "/api/predict/landslide", "predict (2nd call)")
timed("GET", "/disasters/landslides", "page")

ok = d1 < 3.0 and p1 < 5.0
print("TIMING_OK" if ok else "TIMING_STILL_SLOW")