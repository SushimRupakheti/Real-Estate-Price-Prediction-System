import InfrastructureAnalysis from "./InfrastructureAnalysis";
import MacroConditionsCard from "./macro/MacroConditionsCard";

const FRIENDLY_NAMES = {
  LOCATION: "Location",
  FACING: "Facing Direction",
  LOCATION_ENCODED: "Location",
  "LAND AREA (sqft)": "Land Area",
  BATHROOM: "Bathrooms",
  BEDROOM: "Bedrooms",
  FLOOR: "Floor",
  "ROAD ACCESS (ft)": "Road Access",
  "PROPERTY AGE": "Property Age",
  AREA_PER_BEDROOM: "Area per Bedroom",
  TOTAL_ROOMS: "Total Rooms",
  FACING_ENCODED: "Facing Direction",
  HAS_PARKING: "Parking",
  HAS_BALCONY: "Balcony",
  HAS_GARDEN: "Garden",
  HAS_MODULAR_KITCHEN: "Modular Kitchen",
  IS_NEW: "New Property",
};

function formatPrice(value) {
  return Math.round(value || 0).toLocaleString("en-IN");
}

function formatCrore(value) {
  return ((value || 0) / 10000000).toFixed(2);
}

function formatContribution(value) {
  const absolute = Math.abs(value || 0);
  const sign = value >= 0 ? "+" : "−";
  if (absolute >= 10000000) return `${sign}Rs. ${(absolute / 10000000).toFixed(2)} cr`;
  if (absolute >= 100000) return `${sign}Rs. ${(absolute / 100000).toFixed(1)} L`;
  return `${sign}Rs. ${Math.round(absolute).toLocaleString("en-IN")}`;
}

function EstimatedPriceCard({ result, locationLabel }) {
  const price = result?.predicted_price;

  if (!price) {
    return (
      <section className="h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Estimated current price</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Complete the property details and select a location to generate an estimate.
            </p>
          </div>
        </div>
        <div className="mt-6 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-5 py-8 text-center">
          <p className="text-sm font-medium text-slate-600">Your estimate will appear here</p>
          <p className="mt-1 text-xs text-slate-400">No price has been calculated yet.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="h-full rounded-2xl border border-blue-200 bg-white p-6 shadow-sm ring-1 ring-blue-50">
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-start gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Estimated current price</h2>
            <p className="mt-1 text-xs text-slate-500">Present-day model estimate</p>
          </div>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-medium text-slate-600">
          Estimate ready
        </span>
      </div>
      <div className="min-w-0 pt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Estimated price</p>
        <p className="mt-3 text-3xl font-bold leading-none tracking-tight text-blue-800 sm:text-4xl">
          Rs. {formatPrice(price)}
        </p>
        <p className="mt-2 text-base font-medium text-slate-600">
          Rs. {formatCrore(price)} crore
        </p>
        <p className="mt-6 flex items-center gap-2 border-t border-slate-100 pt-4 text-sm text-slate-600">
          <span className="inline-block h-2 w-2 rounded-full bg-blue-600" aria-hidden="true" />
          <span className="truncate">Based on the submitted property details for {locationLabel || "the selected location"}</span>
        </p>
        <p className="mt-2 text-xs leading-5 text-slate-400">
          This is a present-day model estimate, not a valuation certificate or future-price forecast.
        </p>
      </div>
    </section>
  );
}

function KeyFactorsCard({ result, form, locationLabel }) {
  const fallback = [
    { feature: "LOCATION_ENCODED", label: `Location (${locationLabel || "selected"})`, pct: 35 },
    { feature: "LAND AREA (sqft)", label: `Land Area (${form.land_area || 1500} sq ft)`, pct: 25 },
    { feature: "ROAD ACCESS (ft)", label: `Road Access (${form.road_access || 12} ft)`, pct: 15 },
    { feature: "PROPERTY AGE", label: `Property Age (${form.property_age || 10} years)`, pct: 10 },
    { feature: "HAS_PARKING", label: "Amenities", pct: 15 },
  ];

  const allShapRows = result?.shap_values || [];
  const shapRows = allShapRows.slice(0, 5);
  const otherContribution = allShapRows
    .slice(5)
    .reduce((total, item) => total + item.shap_value, 0);
  const displayedShapRows = otherContribution
    ? [...shapRows, { feature: "OTHER_FEATURES", shap_value: otherContribution }]
    : shapRows;
  const maxVal = displayedShapRows.length
    ? Math.max(...displayedShapRows.map((item) => Math.abs(item.shap_value))) || 1
    : 1;
  const rows = displayedShapRows.length
    ? displayedShapRows.map((item) => ({
        feature: item.feature,
        label: item.feature === "LOCATION"
          ? `Location (${locationLabel || "selected"})`
          : item.feature === "OTHER_FEATURES" ? "Other features combined" : FRIENDLY_NAMES[item.feature] || item.feature,
        pct: Math.round((Math.abs(item.shap_value) / maxVal) * 100),
        contribution: formatContribution(item.shap_value),
        direction: item.shap_value >= 0 ? "Raised estimate" : "Lowered estimate",
      }))
    : fallback;

  return (
    <div className="h-full rounded-2xl border border-indigo-200 border-l-4 border-l-indigo-500 bg-white p-6 shadow-sm ring-1 ring-indigo-50">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div><h3 className="text-sm font-semibold text-slate-900">
        Why this estimate?
      </h3>
      <p className="mt-1 text-xs text-slate-500">Signed contribution from the model baseline; location categories are combined.</p></div>
      <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-[10px] font-semibold text-indigo-700">MODEL EXPLANATION · SHAP</span></div>
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.feature} className="grid grid-cols-[minmax(0,1fr)_96px_78px] items-center gap-2 text-xs">
            <span className="min-w-0"><span className="block truncate text-slate-700">{row.label}</span>{row.direction && <span className={`mt-0.5 block text-[10px] ${row.direction === "Raised estimate" ? "text-emerald-600" : "text-amber-600"}`}>{row.direction}</span>}</span>
            <div className="h-1.5 rounded-full bg-slate-100">
              <div
                className={`h-1.5 rounded-full ${row.direction === "Raised estimate" ? "bg-emerald-500" : "bg-amber-500"}`}
                style={{ width: `${Math.min(row.pct, 100)}%` }}
              />
            </div>
            <span className="text-right font-medium tabular-nums text-slate-600">{row.contribution || `${row.pct}%`}</span>
          </div>
        ))}
      </div>
      {Number.isFinite(result?.shap_base_value) && <div className="mt-4 border-t border-indigo-100 pt-3 text-[11px] leading-5 text-slate-500">
        Baseline: Rs. {formatPrice(result.shap_base_value)}. All feature contributions reconcile to this estimate
        {Math.abs(result.shap_additivity_error || 0) > 1 ? ` (rounding difference: Rs. ${formatPrice(Math.abs(result.shap_additivity_error))})` : ""}.
      </div>}
    </div>
  );
}

export default function PredictionDashboard({ result, form, locationLabel, propertyPoint }) {
  return (
    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12 lg:col-span-5">
        <EstimatedPriceCard result={result} locationLabel={locationLabel} />
      </div>
      {result && <div className="col-span-12 lg:col-span-7">
          <KeyFactorsCard result={result} form={form} locationLabel={locationLabel} />
        </div>}
      {result && <div className="col-span-12"><MacroConditionsCard result={result} /></div>}
      {result && <div className="col-span-12"><InfrastructureAnalysis
          locationLabel={locationLabel}
          baselinePrice={result.predicted_price}
          pointOverride={propertyPoint}
          hideMap
          autoAnalyze
        /></div>}
    </div>
  );
}
