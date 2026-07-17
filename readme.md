# Nepal House Price Predictor

The application estimates a **current house price** with a fitted sklearn pipeline and exposes it through FastAPI and React. Prediction history is stored in SQLite and SHAP provides model explanations.

## Python environment

The FastAPI runtime was verified as:

```text
C:\Users\ASUS\AppData\Local\Python\pythoncore-3.14-64\python.exe
Python 3.14.5 (64-bit, Windows)
```

Install the pinned environment with:

```powershell
& 'C:\Users\ASUS\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m pip install -r requirements.txt
```

Run the backend from the project root with:

```powershell
& 'C:\Users\ASUS\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m uvicorn src.backend.main:app --reload
```

## Phase 1: current infrastructure context

After receiving a price estimate, a user can place and confirm an approximate property point on an interactive Leaflet/OpenStreetMap map. `POST /infrastructure/analyze` queries Overpass and returns raw current-infrastructure indicators for roads, schools, healthcare, bus stops, markets, banks, parks, and—when geometry permits—road intersections.

Results are cached using coordinates rounded to four decimal places (approximately 11 m latitude and 10 m longitude in Nepal) plus a configuration version. This reduces repeated Overpass calls while avoiding broad neighbourhood-level rounding.

Facility counts use independently calculated straight-line distance to the mapped feature centre and report both raw OSM elements and deduplicated physical places. Deduplication prefers shared OSM references, then normalized names within 150 m, tagged child features contained by a tagged site polygon, and finally near-identical unnamed cross-type representations within 5 m. Schools, colleges, kindergartens, hospitals, clinics, marketplaces, and supermarkets are returned separately. Pharmacies, doctors, ATMs, convenience stores, gardens, playgrounds, and generic shops are excluded from these headline counts.

Each category also returns the sorted OSM places that produce its deduplicated count: displayed name (or `Unnamed facility`), element type and ID, coordinates, straight-line distance, and matched tags. The frontend exposes these through expandable lists, highlights selected places on the Leaflet map, limits initial markers to the nearest five per category, and can export the complete timestamped response as JSON.

Nearest-road distance is measured to the nearest mapped road geometry. Major roads are explicitly limited to motorway, trunk, primary, and secondary classifications; tertiary streets are treated as local/collector roads for this project. Intersection indicators are currently `null`: the lightweight Overpass response is not treated as a validated routable graph, avoiding inflated junction counts.

Phase 1 itself does not calculate a score, value-shift percentage, adjusted price, or future-price forecast. OpenStreetMap coverage and tagging completeness vary by location, and users should manually select the approximate property position.

The legacy `geospatial_features.py` is not an OSM implementation and is not used by this module. Its price-derived location tiers must not be used for current infrastructure analysis.

## API example

```http
POST /infrastructure/analyze
Content-Type: application/json

{"latitude":27.693,"longitude":85.281,"location_name":"Kalanki, Kathmandu"}
```

Run backend tests without real OSM calls:

```powershell
python -m pytest tests/test_infrastructure.py -q
```

## Phase 2: Infrastructure Health Index

`POST /infrastructure/index` is a separate deterministic assessment of the current indicators produced by Phase 1. It does not modify `POST /predict` or `POST /infrastructure/analyze`. It scores six independent categories: Accessibility, Education, Healthcare, Commerce, Public Transport, and Recreation.

Every threshold, classification range, component weight, category weight, description, and missing-value score is stored in [`config/infrastructure_index_rules.json`](config/infrastructure_index_rules.json). The backend reloads this JSON for every index request, so a valid configuration change takes effect without changing Python code or retraining a model. Healthcare uses hospital- and clinic-tagged places and explicitly excludes pharmacies.

The score is calculated as follows:

```text
Existing OSM analysis result
          |
          v
Extract verified distances, road class, and deduplicated counts
          |
          v
Match each indicator to an explicit JSON threshold
          |
          v
Component score × configured component weight
          |
          v
Six category scores × configured category weights
          |
          v
Infrastructure Health Index (0–100) + classification + audit trail
```

The response includes the observed indicator, display value, matched rule, component score, component weight, weighted contribution, category score, category classification, overall score, rule version, and limitations. The React interface shows simple horizontal bars and expandable explanations; it deliberately uses no radar or pie chart.

### Index API request

A coordinate request is:

```http
POST /infrastructure/index
Content-Type: application/json

{
  "latitude": 27.693,
  "longitude": 85.281,
  "location_name": "Kalanki, Kathmandu"
}
```

To avoid another OpenStreetMap request, send `{"analysis": <complete response from POST /infrastructure/analyze>}` instead. This is the form used by the React interface. When coordinates are supplied, the index route obtains the Phase 1 analysis through `InfrastructureService` before scoring it.

An abbreviated response looks like:

```json
{
  "overall_score": 96,
  "classification": "Excellent",
  "categories": {
    "accessibility": {
      "score": 94,
      "classification": "Excellent",
      "reason": "Nearest road: 12 m; matched 'Nearest mapped road within 25 m'.",
      "rules_used": [
        {
          "indicator": "nearest_road_distance_m",
          "observed_value": 12,
          "matched_rule": "Nearest mapped road within 25 m",
          "component_score": 100,
          "component_weight": 0.35,
          "weighted_contribution": 35.0
        }
      ]
    }
  },
  "metadata": {"method": "deterministic_json_rules", "rules_version": "1.0.0"}
}
```

### Reproducible example profiles

These are fixed test profiles, not claims about every place with the same urban label:

| Test profile | Overall IHI | Classification |
|---|---:|---|
| Dense urban profile | 96 | Excellent |
| Suburban profile | 59 | Good |
| Less-developed profile | 3 | Limited |

The examples are covered by `tests/test_infrastructure_index.py`, which also proves deterministic repeatability and verifies that changing a JSON threshold changes the result without a Python modification.

### Separation and limitations

- Current house-price prediction: fitted ML pipeline based on property inputs; exposed by `POST /predict`.
- Infrastructure analysis: raw current OpenStreetMap indicators; exposed by `POST /infrastructure/analyze`.
- Infrastructure Health Index: configurable rule-based interpretation of those current indicators; exposed by `POST /infrastructure/index`.
- Future scenario simulation: not implemented.

The Infrastructure Health Index is **not** a future-price forecast, appreciation estimate, property valuation, or statistically trained model. It does not use the predicted house price. Its accuracy is limited by OpenStreetMap completeness, tagging quality, deduplication assumptions, straight-line distance methodology, and the policy choices expressed in the configurable rules.
