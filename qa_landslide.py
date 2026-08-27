"""QA smoke test for the Landslide Early Warning Unit."""
import json
import os
import time

t0 = time.time()
SEP = "=" * 50

print(SEP)
print("1. LandslideDataManager.fetch_all_landslide_data")
print(SEP)
from app.utils.landslide_data import LandslideDataManager
live = LandslideDataManager.fetch_all_landslide_data()
print("status:", live.get("status"))
print("summary:", json.dumps(live.get("summary"), indent=2))
print("seismic events:", len(live.get("seismic", {}).get("events", [])))
print("soil moisture frac:", live.get("soil", {}).get("soil_moisture_frac"))
print("terrain zones:", len(live.get("terrain", {}).get("zones", [])))

print(SEP)
print("2. train_landslide_models")
print(SEP)
from app.utils.landslide_ml import train_landslide_models
meta = train_landslide_models(force=True)
print("classifier:", meta.get("classifier_kind"))
print("fallback:", meta.get("fallback_model_kind"))
print("n_samples:", meta.get("n_samples"))
print("class_distribution:", meta.get("class_distribution"))

print(SEP)
print("3. predict_landslide")
print(SEP)
from app.utils.landslide_ml import predict_landslide
pred = predict_landslide(include_explanations=True)
print("current_risk:", pred.get("current_risk"),
      "| confidence:", pred.get("risk_confidence_pct"))
print("rule_based_risk:", pred.get("rule_based_risk"))
print("proba:", pred.get("class_probabilities_pct"))
print("next_year:", pred.get("next_year"),
      "| high days this yr:", pred.get("high_hazard_days_this_year"),
      "| predicted next yr:", pred.get("predicted_high_events_next_year"))
print("trend:", pred.get("trend"))
print("risk_surface points:", len(pred.get("risk_surface", [])))
print("shap:", pred.get("explainability", {}).get("shap_feature_importance"))
lime = pred.get("explainability", {}).get("lime_local_explanation") or []
print("lime entries:", len(lime))

print(SEP)
print("4. Saved outputs")
print(SEP)
for f in ["landslide_inputs.json", "landslide_imd.json",
          "landslide_seismic.json", "landslide_soil.json",
          "landslide_terrain.json"]:
    p = os.path.join("data", f)
    size = os.path.getsize(p) if os.path.exists(p) else 0
    print(f, "exists:", os.path.exists(p), "size:", size)
for f in ["landslide_classifier.pkl", "landslide_fallback_model.pkl",
          "landslide_meta.json"]:
    p = os.path.join("models", f)
    print(f, "exists:", os.path.exists(p))

print(SEP)
print(f"Total elapsed: {time.time() - t0:.1f}s")