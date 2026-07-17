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

This phase does **not** calculate an infrastructure score, value-shift percentage, adjusted price, or future-price forecast. OpenStreetMap coverage and tagging completeness vary by location, and users should manually select the approximate property position.

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
