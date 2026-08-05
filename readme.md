# Nepal House Price Predictor

The application estimates a **current house price** with a fitted sklearn pipeline and exposes it through FastAPI and React. Prediction history is stored in SQLite and SHAP provides model explanations.

## Python environment

The FastAPI runtime was verified as:

```text
C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe
Python 3.13 (64-bit, Windows)
```

Install the pinned environment with:

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m pip install -r requirements.txt
```

Run the backend from the project root with:

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m uvicorn src.backend.main:app --reload
```

## Phase 1: current infrastructure context

Before entering property details, a user searches for a recognised area and confirms the exact property point on an interactive Leaflet/OpenStreetMap map. `POST /infrastructure/analyze` queries Overpass and returns raw current-infrastructure indicators for roads, schools, healthcare, bus stops, markets, banks, parks, and—when geometry permits—road intersections.

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

## Phase 3: Future Infrastructure Planning

`POST /scenarios/simulate` supports a separate planning and exploratory-analysis interface. It copies the current infrastructure indicators, applies only the selected planned or proposed development to that temporary copy, and recalculates both states through the existing `InfrastructureIndexService`. It never writes to OpenStreetMap and does not alter the Phase 1 response.

All supported actions, facility caps, total-quantity cap, road hierarchy, maximum distance reductions, index-change bands, percentage ranges, score caps, disclaimer, and configuration version are stored in [`config/scenario_rules.json`](config/scenario_rules.json). The file is loaded and validated for every request.

```text
Current OSM indicators + present ML price
                    |
                    v
          Deep-copy current indicators
                    |
                    v
 Apply configured hypothetical changes to copy
                    |
                    v
 Reuse InfrastructureIndexService for both states
                    |
                    v
 Current IHI vs scenario IHI + sequential rule contributions
                    |
                    v
 Configured illustrative percentage and value range
```

### Scenario API example

```http
POST /scenarios/simulate
Content-Type: application/json

{
  "baseline_price": 40000000,
  "current_infrastructure": {
    "nearest_road_distance_m": 60,
    "nearest_major_road_distance_m": 850,
    "major_road_type": "secondary",
    "schools": 5,
    "colleges": 1,
    "kindergartens": 1,
    "hospitals": 2,
    "clinics": 2,
    "bus_stops": 3,
    "marketplaces": 1,
    "supermarkets": 1,
    "banks": 3,
    "parks": 2
  },
  "changes": [
    {"type": "major_road_distance", "new_distance_m": 180},
    {"type": "road_upgrade", "new_road_type": "primary"}
  ]
}
```

An abbreviated response is:

```json
{
  "baseline_price": {"amount": 40000000, "formatted": "NPR 4.00 Crore"},
  "current": {"overall_index": 59, "classification": "Good", "category_scores": {}},
  "scenario": {"overall_index": 65, "classification": "Good", "index_change": 6, "category_scores": {}, "category_score_differences": {}},
  "value_shift": {
    "classification": "Strong Positive Scenario",
    "minimum_percent": 3,
    "maximum_percent": 7,
    "minimum_value": 41200000,
    "maximum_value": 42800000,
    "method": "rule_based_infrastructure_scenario",
    "is_forecast": false,
    "statistically_validated": false
  },
  "rule_contributions": [],
  "metadata": {
    "rules_version": "1.0.0",
    "temporary_copy": true,
    "disclaimer": "This result is a configurable, rule-based what-if analysis. It is not a statistically trained future-price forecast, investment guarantee, or professional valuation."
  }
}
```

The frontend appears after the current Infrastructure Health Index. A single opt-in checkbox opens a grouped development selector, followed by only the one additional choice needed for that project. Road-access plans use readable proximity bands such as **within 250 m**, **within 500 m**, **within 1 km**, and **within 2 km**; options that would worsen the current mapped distance are automatically hidden. The user then chooses **Evaluate Future Scenario**. This progressive-disclosure design also provides a live selection summary, current-versus-scenario comparison, impact explanation, rule contributions, reset/error/loading states, and a visibly separated illustrative value range.

### System boundaries

1. The ML model estimates a present property value from property inputs.
2. OpenStreetMap analysis describes currently mapped nearby infrastructure.
3. The Infrastructure Health Index summarizes that current infrastructure using configured rules.
4. Future Infrastructure Planning evaluates a selected planned, proposed, or hypothetical development and maps the resulting IHI difference to a configured illustrative value range.

No historical before-and-after infrastructure price-change dataset was used. The percentage bands are policy assumptions in JSON, not fitted coefficients. Consequently, the scenario value is not a guaranteed price increase, expected appreciation, future predicted value, investment recommendation, or professional valuation.

The initial UI intentionally exposes improvement-only actions. An empty scenario demonstrates minimal change. Negative index-change bands are configured and tested for future degradation/removal actions, but the API currently rejects facility removal, farther-road changes, and road downgrades. Scenario history is not persisted in this phase.

## Guided frontend experience

The React interface uses a progressive three-step journey:

1. **Investment location:** search a recognised area, let the map recenter, adjust the marker by clicking or dragging, and confirm the coordinates.
2. **Property details:** enter size, building, accessibility, age, facing direction, and amenities in grouped cards. Encoded model fields remain internal.
3. **Property analysis:** review present estimated value, nearby infrastructure highlights, Infrastructure Health Index, neutral location strengths and considerations, separate data-confidence indicators, advanced disclosures, and optional Future Infrastructure Planning.

Raw OSM identifiers, mapped-facility lists, scoring-rule explanations, SHAP factors, and JSON export are collapsed by default. Completed current analyses are stored only in the browser under `propertyAnalyses` and can be compared on the **Compare Locations** page. This page compares two current analyses and deliberately excludes hypothetical scenarios. Browser-local comparison records are not written to the backend database.

## Macroeconomic adjustment layer

The fitted property model is unchanged. After `/predict` calculates `base_price`, the backend optionally reads the latest `validated` row from `macro_indicators` and applies a separate, auditable Market Adjustment Index (MAI). A missing macro record never blocks the base price, SHAP, or infrastructure analysis. No valuation endpoint contacts NRB.

Because this repository has no official historical real-estate calibration target, fewer than three comparable periods use `documented_rule_assumptions` from `config/macro_adjustment_rules.json`. The assumed neutral baselines, sensitivities, directions, and per-indicator caps are visible and editable; the total is capped at 3%. This method is explicitly not empirically calibrated. Once at least three comparable periods exist, the service switches to its robust historical median/MAD calculation. Housing and Utilities CPI is always labelled separately from residential house-price inflation.

Endpoints:

- `GET /api/macro/current` reads the newest validated database record.
- `POST /api/macro/adjust` accepts `{"predicted_price": 25000000}`.
- `POST /api/macro/scenario` applies percentage-point economic assumptions after the current layer. Infrastructure projects receive no premium until an evidence-based impact calibration exists.

The standalone updater is the only component permitted to access official NRB sources:

```powershell
python -m src.backend.jobs.update_nrb_macro
```

It discovers a publication under the configured official archive, permits HTTPS NRB domains only, checks signatures and size, calculates SHA-256, rejects duplicate checksums, extracts XLSX first or PDF when selected, validates completeness/plausibility, inserts transactionally, and preserves the previous valid record on failure. Review the extracted measurement bases and reference period before production use because NRB workbook layouts and reporting bases can change. Configuration is documented in `.env.example`.

Do not run the updater inside FastAPI. On Windows Task Scheduler, create a weekly task whose program is the environment's Python executable, arguments are `-m src.backend.jobs.update_nrb_macro`, and start-in directory is this repository. On cron, the equivalent is:

```cron
15 3 * * 1 cd /path/to/prediction_model && /path/to/venv/bin/python -m src.backend.jobs.update_nrb_macro
```

Install and test:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/test_macro_adjustment.py tests/test_macro_validation.py -q
```

The SQLite table and additive prediction-history columns are created automatically on backend startup. For a managed production database, translate the definitions in `src/backend/database.py` into the deployment's normal migration tool rather than relying on SQLite `ALTER TABLE` statements.
