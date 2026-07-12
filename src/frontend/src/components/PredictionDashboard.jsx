import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import LocationMap from "./LocationMap";

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

function HouseIllustration() {
  return (
    <div className="relative hidden h-24 w-36 shrink-0 md:block">
      <div className="absolute right-6 top-1 h-16 w-28 rounded-full bg-blue-50" />
      <div className="absolute right-1 top-6 h-14 w-32 rounded-full bg-blue-50" />
      <div className="absolute bottom-1 right-12 h-16 w-24 rounded-t-md border border-blue-200 bg-blue-50 shadow-inner" />
      <div className="absolute bottom-16 right-10 h-10 w-20 rotate-45 rounded-sm bg-blue-500" />
      <div className="absolute bottom-4 right-24 h-8 w-6 rounded-t bg-blue-600" />
      <div className="absolute bottom-11 right-20 h-5 w-5 border border-blue-500 bg-white" />
      <div className="absolute bottom-11 right-7 h-5 w-5 border border-blue-500 bg-white" />
      <div className="absolute bottom-2 right-0 rounded-lg bg-blue-700 px-3 py-4 text-sm font-bold text-white shadow-lg">
        Rs
      </div>
    </div>
  );
}

function EstimatedPriceCard({ result, locationLabel }) {
  const price = result?.predicted_price || 45200000;
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center justify-between min-h-[132px]">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-gray-700">Estimated Price</p>
        <p className="mt-2 text-3xl leading-none font-bold text-blue-700">
          Rs. {formatPrice(price)}
        </p>
        <p className="text-base font-medium text-blue-700">
          (Rs. {formatCrore(price)} Crore)
        </p>
        <p className="mt-2 truncate text-xs text-green-600">
          ↑ Scenario estimate for {locationLabel || "selected location"}
        </p>
      </div>
      <HouseIllustration />
    </div>
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
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 min-h-[176px]">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Key Factors Influencing Price
      </h3>
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.feature} className="grid grid-cols-[minmax(0,1fr)_96px_34px] items-center gap-2 text-xs">
            <span className="text-gray-700 truncate">{row.label}</span>
            <div className="h-2 rounded-full bg-gray-100">
              <div
                className="h-2 rounded-full bg-blue-600"
                style={{ width: `${Math.min(row.pct, 100)}%` }}
              />
            </div>
            <span className="text-right font-medium text-gray-600">{row.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MacroIndicatorsCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 min-h-[176px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">NRB Macro Inflation Signals</h3>
          <p className="mt-1 text-[11px] text-gray-400">Potential influence over the next 3–6 months</p>
        </div>
        <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-700">
          Outlook
        </span>
      </div>
      <div className="mt-3 space-y-2">
        {NRB_MACRO_INDICATORS.map((item) => (
          <div key={item.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-lg bg-slate-50 px-3 py-2">
            <div className="min-w-0">
              <p className="text-xs font-semibold text-gray-700">{item.label}</p>
              <p className="truncate text-[10px] text-gray-400">{item.detail}</p>
            </div>
            <div className="text-right">
              <p className="text-xs font-bold text-blue-700">{item.value}</p>
              <p className={`text-[10px] font-medium ${item.signal === "Upward" ? "text-orange-600" : "text-emerald-600"}`}>
                {item.signal}
              </p>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[10px] leading-4 text-gray-400">
        Directional context only; these indicators do not directly forecast an individual property price.
      </p>
    </div>
  );
}

function AboutPredictionCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 min-h-[164px]">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">About This Prediction</h3>
      <p className="text-xs leading-5 text-gray-500">
        This price is predicted using a machine learning model trained on historical
        house sale data from different locations in Nepal.
      </p>
      <div className="mt-4 rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-800">
        Model Accuracy (R² Score): 0.7287
      </div>
      <div className="mt-2 text-xs text-gray-400">
        Predicted on: {new Date().toLocaleDateString("en-IN", {
          year: "numeric",
          month: "long",
          day: "numeric",
        })}
      </div>
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
  return (
    <div className="grid grid-cols-12 gap-3">
      <div className="col-span-12">
        <EstimatedPriceCard result={result} locationLabel={locationLabel} />
      </div>
      <div className="col-span-6">
        <KeyFactorsCard result={result} form={form} locationLabel={locationLabel} />
      </div>
      <div className="col-span-6">
        <MacroIndicatorsCard />
      </div>
      <div className="col-span-6">
        <LocationMap locationLabel={locationLabel} compact />
      </div>
      <div className="col-span-6">
        <AboutPredictionCard />
      </div>
      <div className="col-span-12">
        <AlternativeLocationsCard result={result} locationLabel={locationLabel} />
      </div>
    </div>
  );
}
