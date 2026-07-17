import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import LocationMap from "./LocationMap";
import InfrastructureAnalysis from "./InfrastructureAnalysis";

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

const NRB_MACRO_INDICATORS = [
  { label: "CPI inflation", value: "5.4%", signal: "Upward", detail: "Broad price pressure" },
  { label: "Housing inflation", value: "8.2%", signal: "Upward", detail: "Construction and rent pressure" },
  { label: "Avg. lending rate", value: "11.5%", signal: "Restraining", detail: "Higher borrowing cost" },
];

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
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">2</span>
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
    <section className="h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-start gap-3">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">2</span>
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
        <p className="mt-3 text-3xl font-bold leading-none tracking-tight text-slate-950 sm:text-4xl">
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
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 min-h-[176px]">
      <h3 className="text-sm font-semibold text-slate-800 mb-1">
        Price factor breakdown
      </h3>
      <p className="mb-4 text-xs text-slate-400">Relative influence for this estimate</p>
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.feature} className="grid grid-cols-[minmax(0,1fr)_96px_34px] items-center gap-2 text-xs">
            <span className="text-slate-700 truncate">{row.label}</span>
            <div className="h-1.5 rounded-full bg-slate-100">
              <div
                className="h-1.5 rounded-full bg-slate-700"
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

function MacroIndicatorsCard() {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 min-h-[176px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Market context</h3>
          <p className="mt-1 text-[11px] text-slate-400">Reference indicators from NRB data</p>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-semibold text-slate-600">
          Context only
        </span>
      </div>
      <div className="mt-3 space-y-2">
        {NRB_MACRO_INDICATORS.map((item) => (
          <div key={item.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-lg bg-slate-50 px-3 py-2">
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-700">{item.label}</p>
              <p className="truncate text-[10px] text-slate-400">{item.detail}</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-bold text-slate-800">{item.value}</p>
              <p className="text-[10px] font-medium text-slate-500">
                {item.signal}
              </p>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[10px] leading-4 text-slate-400">
        Directional context only; these indicators do not directly forecast an individual property price.
      </p>
    </div>
  );
}

function AlternativeLocationsCard({ result, locationLabel }) {
  const [history, setHistory] = useState([]);
  const price = result?.predicted_price || 45200000;

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/history")
      .then((res) => setHistory(res.data))
      .catch(() => setHistory([]));
  }, [result?.predicted_price]);

  const alternatives = useMemo(() => {
    if (!history.length || !price) return [];
    const selected = String(locationLabel || "").toLowerCase();
    const min = price * 0.85;
    const max = price * 1.15;

    const grouped = new Map();
    history
      .filter((item) => item.location_label)
      .filter((item) => String(item.location_label).toLowerCase() !== selected)
      .filter((item) => item.predicted_price >= min && item.predicted_price <= max)
      .forEach((item) => {
        const key = item.location_label;
        const existing = grouped.get(key) || {
          location: key,
          count: 0,
          total: 0,
          closestDiff: Infinity,
          sample: item,
        };
        const diff = Math.abs(item.predicted_price - price);
        existing.count += 1;
        existing.total += item.predicted_price;
        if (diff < existing.closestDiff) {
          existing.closestDiff = diff;
          existing.sample = item;
        }
        grouped.set(key, existing);
      });

    return Array.from(grouped.values())
      .map((item) => ({
        ...item,
        avgPrice: item.total / item.count,
      }))
      .sort((a, b) => a.closestDiff - b.closestDiff)
      .slice(0, 3);
  }, [history, locationLabel, price]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 min-h-[164px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Alternative Locations</h3>
          <p className="text-xs text-gray-400 mt-1">Same price range from prediction history</p>
        </div>
        <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2 py-1 rounded-full">
          ±15%
        </span>
      </div>

      {alternatives.length === 0 ? (
        <div className="mt-4 rounded-lg bg-gray-50 px-3 py-3 text-xs leading-5 text-gray-500">
          No matching historical alternatives yet. New predictions will make this recommendation smarter.
        </div>
      ) : (
        <div className="mt-4 space-y-2">
          {alternatives.map((item) => (
            <div key={item.location} className="flex items-center justify-between gap-3 rounded-lg bg-gray-50 px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-gray-700">{item.location}</p>
                <p className="text-[11px] text-gray-400">
                  {item.count} similar prediction{item.count > 1 ? "s" : ""}
                </p>
              </div>
              <p className="shrink-0 text-xs font-bold text-blue-700">
                Rs. {formatCrore(item.avgPrice)} Cr
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PredictionDashboard({ result, form, locationLabel }) {
  const [propertyPoint, setPropertyPoint] = useState(null);
  const [mapFacilities, setMapFacilities] = useState([]);
  const [selectedFacility, setSelectedFacility] = useState(null);

  return (
    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12 lg:col-span-5">
        <EstimatedPriceCard result={result} locationLabel={locationLabel} />
      </div>
      <div className="col-span-12 lg:col-span-7">
        <LocationMap
          locationLabel={locationLabel}
          onCoordinateChange={setPropertyPoint}
          onCoordinateConfirm={setPropertyPoint}
          facilities={mapFacilities}
          selectedFacility={selectedFacility}
          onFacilitySelect={setSelectedFacility}
        />
      </div>
      {result && <div className="col-span-12"><InfrastructureAnalysis
          locationLabel={locationLabel}
          pointOverride={propertyPoint}
          hideMap
          onMapFacilitiesChange={setMapFacilities}
          onFacilityFocusChange={setSelectedFacility}
        /></div>}
      {result && <div className="col-span-12 lg:col-span-6">
          <KeyFactorsCard result={result} form={form} locationLabel={locationLabel} />
        </div>}
      {result && <div className="col-span-12 lg:col-span-6">
          <MacroIndicatorsCard />
        </div>}
      {result && <div className="col-span-12">
          <AlternativeLocationsCard result={result} locationLabel={locationLabel} />
        </div>}
    </div>
  );
}
