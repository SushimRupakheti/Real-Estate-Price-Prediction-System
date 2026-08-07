# Nepal Property Insight: Project Technical Reference

## 1. Project purpose

Nepal Property Insight is a full-stack research application for estimating the **present asking price of a house in Nepal** and placing that estimate in its current geographic, infrastructure, and macroeconomic context. It combines a trained scikit-learn regression pipeline, SHAP explanations, a FastAPI service, a React interface, OpenStreetMap-derived indicators, deterministic infrastructure scoring, configurable what-if scenarios, and SQLite persistence.

The system must be understood as several separate analytical layers:

1. **Current house-price estimate:** a fitted machine-learning model predicts a present price from property characteristics.
2. **Model explanation:** SHAP ranks the transformed features that most influenced an individual estimate.
3. **Current infrastructure context:** OpenStreetMap data describes mapped roads and facilities near a user-confirmed point.
4. **Infrastructure Health Index (IHI):** explicit JSON rules convert current infrastructure indicators into a 0–100 score.
5. **Infrastructure scenario:** a configurable, hypothetical change is applied to a copy of the current indicators and mapped to an illustrative value range.
6. **Macroeconomic adjustment:** a separate Market Adjustment Index (MAI) can adjust the base ML estimate using the latest validated Nepal Rastra Bank record.

Only the first layer is the trained property-price model. The IHI, scenario percentage ranges, and fallback macro adjustment are rule-based analytical mechanisms, not additional learned price models.

## 2. Current implementation at a glance

| Area | Implementation |
|---|---|
| Backend | FastAPI, Pydantic, SQLAlchemy, SQLite |
| Frontend | React 19, Axios, Tailwind CSS, Leaflet/React-Leaflet, Recharts |
| ML runtime | scikit-learn pipeline loaded from `models/best_model.joblib` |
| Selected estimator | Gradient Boosting Regressor |
| Explanation | SHAP TreeExplainer, with a LinearExplainer fallback |
| Current map data | OpenStreetMap via Nominatim and Overpass |
| Infrastructure score | Deterministic, JSON-configured weighted index |
| Scenario analysis | Deterministic what-if simulation over copied indicators |
| Macro data | Validated NRB records stored in SQLite; updater runs separately |
| Persistence | `src/backend/predictions.db` and `src/backend/infrastructure_cache.db` |
| Automated tests | Pytest backend tests and React Testing Library component tests |

## 3. Repository structure

```text
prediction_model/
├── config/                         # IHI, scenario, and macro rule sets
├── data/
│   ├── raw/                        # Original scraped/listing dataset
│   └── processed/                  # Cleaned data and fixed train/test split
├── models/                         # Fitted pipelines, metrics, schema, metadata
├── src/
│   ├── backend/                    # FastAPI application and domain modules
│   │   ├── infrastructure/         # OSM query, cache, deduplication, indicators
│   │   ├── infrastructure_index/   # Config loading and deterministic scoring
│   │   ├── scenario/               # Scenario validation and simulation
│   │   ├── macro/                  # NRB ingestion, validation, MAI, scenarios
│   │   └── jobs/                   # Standalone NRB update/import jobs
│   ├── data cleaning/              # Original cleaning script
│   ├── eda/                        # Exploratory analysis scripts
│   ├── frontend/                   # React application
│   ├── model_training/             # Split, train, compare, tune, save scripts
│   └── outliers/                   # Outlier-analysis script
├── tests/                          # Backend unit/integration-style tests
├── visualizations/chart images/    # EDA and model-analysis figures
├── geospatial_features.py          # Legacy experimental price-derived features
├── hedonic_baseline.py             # Separate statistical/hedonic analysis
├── segment_stability.py            # Segment performance/stability analysis
├── requirements.txt
├── package.json
└── readme.md                       # Earlier phase-oriented notes
```

Generated frontend build files, local databases, temporary NRB files, installed `node_modules`, and model artifacts are also currently present in the working tree.

## 4. Data and preprocessing

### 4.1 Dataset inventory

The files currently contain:

| File | Rows | Columns | Distinct locations |
|---|---:|---:|---:|
| `data/raw/Nepali_house_dataset.csv` | 3,418 | 13 | 504 |
| `data/processed/cleaned_house_data.csv` | 1,082 | 14 | 276 |
| `data/processed/X_train.csv` | 816 | 15 | 231 |
| `data/processed/X_test.csv` | 205 | 15 | 97 |

The final model comparison uses 1,021 rows: 816 training rows and 205 held-out test rows. This is smaller than the 1,082-row cleaned file because `load_clean_data()` excludes listings with more than 10 bedrooms, more than 10 bathrooms, or a price above NPR 100,000,000.

The raw dataset is listing data and the target is the advertised `PRICE`; therefore, the output should be described as an estimated present **listing/asking price**, not a verified transaction price or formal valuation.

### 4.2 Cleaning performed by `src/data cleaning/cleaning.py`

The cleaning script:

- retains titles containing “House for Sale”;
- parses crore, lakh, and plain-number price strings into NPR;
- removes rows without a usable price;
- converts aana (`342.25 sq ft`) and ropani (`5,476 sq ft`) land units to square feet;
- removes `BUILDUP AREA` because of missingness;
- converts road-access ranges such as `12-18` feet to their midpoint;
- normalizes facing text;
- derives property age as `2082 - BUILT YEAR` using a fixed Bikram Sambat reference year;
- converts amenity lists into parking, balcony, garden, and modular-kitchen flags;
- median-imputes several numeric fields and mode-imputes facing;
- removes unused raw columns and writes `cleaned_house_data.csv`.

Important reproducibility note: this script contains absolute Windows paths and a fixed `CURRENT_YEAR_BS = 2082`. Those should be made project-relative and parameterized before treating the cleaning pipeline as portable or automatically repeatable in future years.

### 4.3 Model-time feature engineering

`src/model_training/compare_model.py` performs the final filtering and creates:

- `AREA_PER_BEDROOM = LAND AREA (sqft) / BEDROOM`;
- `TOTAL_ROOMS = BEDROOM + BATHROOM`;
- `IS_NEW = 1` when `PROPERTY AGE <= 2`, otherwise `0`.

It removes legacy `LOCATION_ENCODED` and `FACING_ENCODED` columns if they exist. Location and facing are treated as categorical strings and one-hot encoded inside the fitted pipeline. This is important: the production model does **not** use a price-derived numerical location encoding.

The 15 raw model features are:

```text
LOCATION, FACING, FLOOR, BEDROOM, BATHROOM, LAND AREA (sqft),
ROAD ACCESS (ft), PROPERTY AGE, HAS_PARKING, HAS_BALCONY,
HAS_GARDEN, HAS_MODULAR_KITCHEN, AREA_PER_BEDROOM,
TOTAL_ROOMS, IS_NEW
```

Numeric inputs are median-imputed and standardized. Categorical inputs are most-frequent-imputed and one-hot encoded with unknown categories ignored. All preprocessing is fitted within the scikit-learn `Pipeline`, including within cross-validation folds, which prevents test-set preprocessing leakage.

## 5. Model development and evaluation

### 5.1 Experimental design

- Random train/test split: 80/20
- Random state: 42
- Training rows: 816
- Test rows: 205
- Cross-validation: five-fold shuffled KFold on the training set only
- Selection rule: highest held-out test R²
- Persisted production artifact: `models/best_model.joblib`

The comparison script evaluates Linear Regression, Ridge Regression, Gradient Boosting, XGBoost, and LightGBM. The persisted metadata records Gradient Boosting as the selected model.

### 5.2 Recorded comparison metrics

| Model | Test MAE (NPR) | Test RMSE (NPR) | Test R² | CV mean R² ± SD |
|---|---:|---:|---:|---:|
| Linear Regression | 7,834,028 | 10,975,450 | 0.5803 | 0.5831 ± 0.0291 |
| Ridge Regression | 7,349,958 | 10,466,744 | 0.6183 | 0.6101 ± 0.0369 |
| **Gradient Boosting** | **6,805,183** | **9,786,851** | **0.6663** | **0.6164 ± 0.0423** |
| XGBoost | 7,075,120 | 10,215,018 | 0.6365 | 0.5974 ± 0.0415 |
| LightGBM | 7,620,906 | 10,929,366 | 0.5838 | 0.5667 ± 0.0455 |

These values come from `models/metrics.json`. Separate linear and ridge scripts have their own later metric files, so their numbers differ slightly from the shared comparison run; they should not be mixed into the comparison table.

### 5.3 Interpretation and limitations

An R² of approximately 0.666 means the selected model explains about two-thirds of held-out price variation in this particular split. An MAE of approximately NPR 6.81 million is large enough that the result must be presented as an exploratory estimate. There is no prediction interval, external validation set, temporal split, transaction-price validation, or documented production drift monitor.

Model selection used the same held-out test split to choose the winning estimator. For stronger research methodology, a validation set or nested cross-validation should select the model and a final untouched test set should report performance.

### 5.4 SHAP explanations

The backend transforms the submitted raw row with the fitted preprocessor and applies SHAP to the estimator. It returns transformed feature names and SHAP values sorted by absolute magnitude. The UI displays the five largest absolute effects as relative bars.

The displayed percentages are normalized visual magnitudes, not probabilities, confidence levels, or shares of the price. Because location and facing are one-hot encoded, SHAP may return category-specific transformed names rather than the friendly base names listed in the UI mapping.

## 6. Runtime prediction flow

```text
User selects a recognised location and confirms map coordinates
                         |
                         v
User enters property attributes and amenities
                         |
                         v
POST /predict derives area/bedroom, total rooms, and new-property flag
                         |
                         v
Fitted preprocessing + Gradient Boosting pipeline predicts base price
                         |
             +-----------+-----------+
             |                       |
             v                       v
       SHAP explanation       Optional macro adjustment
             |                       |
             +-----------+-----------+
                         v
Prediction saved in SQLite and returned to the React dashboard
                         |
                         v
Confirmed coordinates trigger current OSM infrastructure analysis
                         |
                         v
IHI and optional hypothetical scenario are calculated separately
```

At runtime, `location_label` becomes the categorical `LOCATION` model value and `facing_encoded` is converted through a fixed eight-direction mapping. The request still requires `location_encoded`, and the value is stored in history, but `model.make_frame()` intentionally ignores it. This is a legacy API field and should eventually be removed or made optional through a versioned contract.

## 7. Backend API

FastAPI creates interactive documentation at `/docs` and OpenAPI JSON at `/openapi.json` when the server is running.

| Method and path | Purpose |
|---|---|
| `GET /` | Health-style running message |
| `POST /predict` | Base ML prediction, SHAP values, and optional current macro adjustment |
| `GET /history` | All persisted predictions, newest first |
| `GET /stats` | Selected metrics and model-comparison data |
| `GET /locations` | 111 hard-coded recognised UI locations and legacy numeric values |
| `GET /shap-importance` | Global mean absolute SHAP importance over training data |
| `POST /infrastructure/geocode` | Resolve a Nepal location name using Nominatim |
| `POST /infrastructure/analyze` | Obtain current OSM road and facility indicators |
| `POST /infrastructure/index` | Calculate the deterministic IHI |
| `POST /scenarios/simulate` | Evaluate a hypothetical infrastructure change |
| `GET /api/macro/current` | Return the newest validated macro record |
| `POST /api/macro/adjust` | Apply the current MAI to a supplied price |
| `POST /api/macro/scenario` | Apply user-supplied economic assumptions |

### 7.1 Prediction request

```json
{
  "floor": 2.5,
  "bedroom": 3,
  "bathroom": 2,
  "land_area": 1369,
  "road_access": 12,
  "property_age": 8,
  "has_parking": 1,
  "has_balcony": 1,
  "has_garden": 0,
  "has_modular_kitchen": 1,
  "location_encoded": 35000000,
  "location_label": "Kalanki, Kathmandu",
  "facing_encoded": 2
}
```

The response contains `predicted_price`, a crore-formatted string, ordered `shap_values`, unchanged `base_price`, an optional `macro_adjustment`, and `macro_data_available`.

Current validation gaps should be acknowledged: most prediction fields only have type validation, binary flags are not constrained to 0/1, facing codes are not range-constrained, and a bedroom value of zero causes division by zero before inference. The React form reduces some invalid input but does not replace backend validation.

## 8. Current infrastructure analysis

### 8.1 Source and query

The location picker first calls Nominatim with a Nepal country constraint. After the user confirms or adjusts the map marker, `POST /infrastructure/analyze` sends the exact coordinates to the backend. The backend queries two Overpass endpoints with retry/backoff and requests:

- all mapped highway ways within 1 km;
- motorway, trunk, primary, or secondary ways within 2 km;
- schools, colleges, kindergartens, marketplaces, banks, bus stops, and supermarkets within 1 km;
- hospitals, clinics, and parks within 2 km.

Nearest-road distance uses the nearest point on available road geometry. Facility distance is haversine straight-line distance to the mapped point or calculated feature centre; it is not route distance or travel time.

### 8.2 Facility categorization and deduplication

The response separates schools, colleges, kindergartens, hospitals, clinics, bus stops, marketplaces, supermarkets, banks, and parks. Each category reports raw OSM element count, deduplicated physical-place count, search radius, and a distance-sorted list of contributing places.

Potential duplicate representations are merged when they share a recognized reference, one lies inside the other’s polygon, normalized names match within 150 m, or unnamed cross-type objects with identical matched tags are within 5 m. Pharmacies, doctors, ATMs, convenience shops, playgrounds, gardens, and generic shops are not included in the headline categories.

Intersection fields are deliberately `null`; the lightweight Overpass geometry is not treated as a validated routable graph.

### 8.3 Cache and failure behavior

Successful results are cached in `src/backend/infrastructure_cache.db` for 24 hours. The key uses latitude and longitude rounded to four decimals plus configuration version `phase1-v6-transparent-places`, approximately a 10–11 m coordinate grid in Nepal. If live Overpass fails after a cache entry expires, the last successful entry can be returned with `stale: true`; without a cached entry the API returns HTTP 503.

This layer describes currently mapped infrastructure only. Coverage, tagging, geometry, and update recency depend on OpenStreetMap contributors.

## 9. Infrastructure Health Index

`POST /infrastructure/index` accepts either coordinates or a complete existing infrastructure analysis. The frontend sends the existing response to avoid a second Overpass call.

`config/infrastructure_index_rules.json` defines every threshold, component weight, category weight, missing-indicator score, classification, description, and version. It is loaded for each index request, so valid rule changes take effect without model retraining.

The six category weights are:

| Category | Weight |
|---|---:|
| Accessibility | 22% |
| Education | 18% |
| Healthcare | 18% |
| Public transport | 17% |
| Commerce | 15% |
| Recreation | 10% |

Each component is matched to a configured numeric or categorical band. Component scores are combined within a category, and category scores are combined into a rounded 0–100 overall score. Classifications are Excellent (85–100), Very Good (70–84), Good (55–69), Moderate (35–54), and Limited (0–34).

The response includes an audit trail containing observed values, display values, matched rules, component scores, weights, contributions, category scores, classifications, rule version, and limitations. The IHI is not trained on house prices and must not be described as a price predictor.

## 10. Future infrastructure scenario

`POST /scenarios/simulate` deep-copies current indicators, applies only validated hypothetical improvements, and recalculates the current and scenario IHI through the same `InfrastructureIndexService`. It does not write to OpenStreetMap, alter the original analysis, retrain the model, or persist scenario history.

Supported configuration includes additions of schools, colleges, kindergartens, hospitals, clinics, bus stops, marketplaces, supermarkets, banks, and parks; reduced access-road or major-road distance; and major-road upgrades. Per-action caps, a total quantity cap of 20, distance-reduction caps, and road hierarchy are defined in `config/scenario_rules.json`.

The IHI change is mapped to configured illustrative price-shift bands:

| IHI change | Classification | Configured shift |
|---:|---|---:|
| -100 to -6 | Strong Negative Scenario | -8% to -3% |
| -5 to -3 | Negative Scenario | -4% to -1% |
| -2 to 2 | Minimal Change | 0% to 1% |
| 3 to 5 | Moderate Positive Scenario | 1% to 3% |
| 6 to 10 | Strong Positive Scenario | 3% to 7% |
| 11 to 100 | Major Positive Scenario | 5% to 10% |

Negative bands exist for future extensibility, but the present API/UI accepts improvement-oriented actions and rejects removals, farther roads, and road downgrades. The percentage ranges are policy assumptions; no historical before/after infrastructure-price dataset was used to estimate them. Scenario outputs are not forecasts, expected appreciation, investment guarantees, or professional valuations.

## 11. Macroeconomic adjustment

After the base prediction, the backend attempts to read the newest `validated` macro record. If none is available, the prediction and SHAP explanation still succeed and `macro_data_available` is false.

For this project, the macro-adjusted value is interpreted over an **indicative short-term analysis horizon of approximately three to six months**. The currently reviewed backend snapshot represents the NRB reporting period ending mid-June 2026 and was published on 13 July 2026. Its values are stored by the one-time reviewed import job: national CPI inflation 5.22%, commercial-bank lending rate 6.64%, deposit rate 3.29%, private-sector credit growth 6.50%, and remittance growth 38.20%. A verified Housing and Utilities CPI subgroup was unavailable and is therefore stored as missing rather than estimated.

The three-to-six-month period is a **project-defined interpretation horizon**, not a horizon learned by the model or stated as an NRB property-price forecast. The backend converts the monthly macroeconomic snapshot into a bounded analytical adjustment to the base asking-price estimate; it does not use a longitudinal residential price target to test whether that adjustment predicts property values three to six months later. Accordingly, the result should be described as an **indicative three-to-six-month macro-adjusted value**, not a statistically validated inflation forecast, guaranteed future price, or expected appreciation.

The database stores CPI inflation, optional Housing and Utilities CPI, lending rate, deposit rate, credit growth, remittance growth, reference/publication dates, source metadata, measurement bases, checksum, validation status, extraction version, and provisional status.

With fewer than three comparable historical periods, `config/macro_adjustment_rules.json` supplies documented neutral baselines, sensitivities, directions, individual caps, and a total cap of ±3%. These values are explicitly marked `empirically_calibrated: false`. With at least three comparable periods, the service switches to a robust historical median/MAD method.

The standalone updater is the only component intended to contact NRB:

```powershell
python -m src.backend.jobs.update_nrb_macro
```

It restricts domains, validates download signatures and size, calculates a SHA-256 checksum, prevents duplicate sources, extracts configured spreadsheet/PDF content, validates plausibility/completeness, and inserts transactionally. NRB formats and measurement bases can change, so extracted records require operational review before production use. The web API itself does not download macro publications during valuation.

Infrastructure projects supplied to the macro-scenario endpoint currently receive no macro premium because no evidence-based impact calibration is implemented.

## 12. Persistence and data ownership

`src/backend/predictions.db` contains:

- the property inputs and prediction;
- base and optional macro-adjusted prices;
- macro adjustment percentage, record ID, date, and calibration version;
- reserved scenario fields;
- the `macro_indicators` table and provenance metadata.

Tables are created on import/startup. Small SQLite-compatible migration helpers add missing columns to existing local databases. Production deployments should use a managed migration process rather than application-time `ALTER TABLE` logic.

Prediction history returned by `GET /history` is backend-persisted. By contrast, completed current location analyses used by **Compare Locations** are stored only in browser `localStorage` under `propertyAnalyses`, capped at 20 records. Those comparison records are not synchronized to SQLite, and hypothetical scenarios are excluded from comparison.

There is currently no authentication, user ownership, pagination at the API level, deletion endpoint, or privacy boundary around prediction history. CORS allows every origin. These are acceptable only for a local research prototype, not a public multi-user deployment.

## 13. Frontend experience

The React application provides five navigation views:

1. **Analyse Property:** a three-step location, property-details, and results flow.
2. **Compare Locations:** comparison of two browser-local completed current analyses.
3. **Saved Estimates:** backend prediction history with charts and client-side pagination.
4. **Model Performance:** model metrics and comparison.
5. **Methodology:** model-card-style explanation.

The analysis journey requires selection from 111 backend-recognised location entries, geocodes the label, lets the user click or drag the marker, and then gathers property details. After prediction, it displays the base estimate, top SHAP factors, optional macro conditions, current infrastructure, IHI, and opt-in scenario simulator.

Frontend API URLs are currently hard-coded to `http://127.0.0.1:8000`; deployment requires an environment-driven base URL or same-origin proxy. The application has no React Router; navigation is local component state, so pages do not have independent URLs.

## 14. Installation and execution

### 14.1 Backend

Create and activate a virtual environment, then install pinned runtime packages:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn src.backend.main:app --reload
```

The pinned file records Python 3.14.5 as the verified environment, but portability should be validated on the target machine. The root `package.json` backend script hard-codes a Python 3.13 executable path and may not match the current interpreter; the module command above is the safer startup method.

### 14.2 Frontend

In a second terminal:

```powershell
cd src/frontend
npm install
npm start
```

The development UI normally opens at `http://localhost:3000`, with the API at `http://127.0.0.1:8000`.

### 14.3 Tests

Backend:

```powershell
python -m pytest -q
```

Frontend:

```powershell
cd src/frontend
npm test -- --watchAll=false
```

The backend suite covers infrastructure indicator extraction/deduplication, caching and stale fallback, IHI determinism/configuration, scenario validation and scoring, and macro adjustment/validation. The frontend has tests for location selection, infrastructure analysis, IHI, scenarios, and location comparison.

Tests were not executable during this documentation audit because no Python command or recorded interpreter path was available in the active shell. This document therefore reports repository evidence and stored metrics, not a fresh test-pass claim.

## 15. Reproducibility gaps and technical debt

The following issues are important for a dissertation, technical report, or production plan:

- `requirements.txt` contains runtime/API packages but omits offline-analysis dependencies imported by repository scripts, including XGBoost, LightGBM, statsmodels, and matplotlib.
- The root npm backend command and cleaning/global-SHAP scripts contain machine-specific absolute Windows paths.
- `LOCATION` values offered by `/locations` are hard-coded, and their accompanying legacy numerical values are still sent as `location_encoded` even though the trained model ignores that number.
- Prediction schemas need explicit realistic ranges and cross-field validation.
- The cleaning script uses a fixed Bikram Sambat year and performs imputations before the final train/test split; although model-pipeline imputation is leakage-safe, the already-cleaned source file reflects these earlier whole-dataset fills.
- Model selection should use a validation strategy separate from final test reporting.
- No uncertainty interval, external validation, temporal validation, fairness/coverage study, or drift monitoring is implemented.
- OSM-derived results inherit map coverage and tagging biases, and straight-line proximity does not measure actual accessibility.
- IHI thresholds, scenario shift bands, and fallback macro sensitivities are expert/policy assumptions rather than statistically estimated relationships.
- Local SQLite, open CORS, unbounded history response, and absent authentication are unsuitable for a public multi-user service.
- Generated files, local databases, temporary downloads, and `node_modules` are present; repository hygiene and deployment packaging should be tightened.
- Some source/UI text and the older README contain mojibake characters (for example corrupted arrows, dashes, and symbols) and should be normalized to UTF-8.

## 16. What is legacy or supplementary

- `geospatial_features.py` is a legacy experiment based on price-derived location tiers and is not used by the OSM infrastructure module or production model. It must not be cited as the current geospatial method.
- `hedonic_baseline.py` is a separate statistical analysis script, not the served production estimator.
- `segment_stability.py` analyzes model performance and SHAP behavior across price/location segments; it is supplementary evaluation rather than runtime logic.
- `notebooks/`, `src/eda/`, `src/outliers/`, and `visualizations/` support exploration and reporting but are not imported by the FastAPI application.
- `models/best_model.pkl` duplicates the selected artifact format; runtime code loads `best_model.joblib`.

## 17. Recommended document framing

A formal report based on this project should separate:

1. problem definition and Nepal housing context;
2. listing dataset provenance, scope, cleaning, and known biases;
3. leakage-aware feature pipeline and model comparison;
4. held-out metrics and their limitations;
5. system architecture and API/frontend implementation;
6. SHAP explainability;
7. OSM infrastructure extraction and deduplication;
8. deterministic IHI design and rule provenance;
9. hypothetical scenario assumptions and non-forecast disclaimer;
10. macro data provenance, validation, and calibration limitations;
11. testing, reproducibility, ethical use, and future work.

The central claim should remain narrow: **the application provides an exploratory present asking-price estimate and auditable contextual analysis for selected Nepal property listings.** It should not claim transaction-price accuracy, causal infrastructure effects, guaranteed appreciation, nationwide coverage, or professional valuation status.

## 18. Source-of-truth files

For future documentation updates, use these files as the primary evidence:

| Subject | Source of truth |
|---|---|
| Runtime routes and orchestration | `src/backend/main.py` and router modules |
| Prediction request/response | `src/backend/schemas.py` |
| Runtime feature conversion and SHAP | `src/backend/model.py` |
| Database schema | `src/backend/database.py` |
| Training design | `src/model_training/compare_model.py` |
| Model results | `models/metrics.json`, `models/model_metadata.json` |
| Feature contract | `models/feature_schema.json` |
| OSM query and indicators | `src/backend/infrastructure/` |
| IHI rules | `config/infrastructure_index_rules.json` |
| Scenario assumptions | `config/scenario_rules.json` |
| Macro assumptions | `config/macro_adjustment_rules.json` |
| Frontend behavior | `src/frontend/src/` |
| Automated expectations | `tests/` and frontend `*.test.jsx` files |

This reference reflects the repository state audited on **6 August 2026**.
