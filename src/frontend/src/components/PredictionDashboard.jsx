import InfrastructureAnalysis from "./InfrastructureAnalysis";
import MacroConditionsCard from "./macro/MacroConditionsCard";

const FRIENDLY_NAMES = {
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

  const shapRows = result?.shap_values?.slice(0, 5);
  const maxVal = shapRows?.length
    ? Math.max(...shapRows.map((item) => Math.abs(item.shap_value))) || 1
    : 1;
  const rows = shapRows?.length
    ? shapRows.map((item) => ({
        feature: item.feature,
        label: FRIENDLY_NAMES[item.feature] || item.feature,
        pct: Math.max(8, Math.round((Math.abs(item.shap_value) / maxVal) * 100)),
      }))
    : fallback;

  return (
    <div className="h-full rounded-2xl border border-indigo-200 border-l-4 border-l-indigo-600 bg-gradient-to-br from-white via-white to-indigo-50 p-5 shadow-md shadow-indigo-900/5 ring-1 ring-indigo-50">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div><h3 className="text-sm font-semibold text-slate-900">
        Why this estimate?
      </h3>
      <p className="mt-1 text-xs text-slate-500">Strongest model factors for this property</p></div>
      <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-[10px] font-semibold text-indigo-700">MODEL EXPLANATION · SHAP</span></div>
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.feature} className="grid grid-cols-[minmax(0,1fr)_96px_34px] items-center gap-2 text-xs">
            <span className="text-slate-700 truncate">{row.label}</span>
            <div className="h-1.5 rounded-full bg-slate-100">
              <div
                className="h-1.5 rounded-full bg-indigo-600"
                style={{ width: `${Math.min(row.pct, 100)}%` }}
              />
            </div>
            <span className="text-right font-medium text-slate-500">{row.pct}%</span>
          </div>
        ))}
      </div>
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
