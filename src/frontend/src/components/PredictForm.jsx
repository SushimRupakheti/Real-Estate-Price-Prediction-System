import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import LocationMap from "./LocationMap";
import PredictionDashboard from "./PredictionDashboard";

const FACING_OPTIONS = [
  [2, "East"], [7, "West"], [3, "North"], [6, "South"],
  [4, "North-East"], [5, "North-West"], [0, "South-East"], [1, "South-West"],
];
const ROAD_ACCESS_OPTIONS = [10, 12, 15, 20, 24, 30, 40];
const inputClass = "mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100";
const FIELD_LIMITS = {
  land_area: { min: 102.675, max: 5886.7, label: "Land area" },
  bedroom: { min: 1, max: 36, label: "Bedrooms" },
  bathroom: { min: 1, max: 34, label: "Bathrooms" },
  floor: { min: 1, max: 7, label: "Floors" },
  property_age: { min: 0, max: 100, label: "Property age" },
};

export function validatePropertyForm(form) {
  return Object.fromEntries(Object.entries(FIELD_LIMITS).flatMap(([name, limits]) => {
    const rawValue = form[name];
    const value = Number(rawValue);
    if (rawValue === "" || !Number.isFinite(value)) return [[name, `${limits.label} is required.`]];
    if (value < limits.min || value > limits.max) {
      const unit = name === "land_area" ? " sq ft" : name === "property_age" ? " years" : "";
      return [[name, `${limits.label} must be between ${limits.min.toLocaleString()} and ${limits.max.toLocaleString()}${unit}.`]];
    }
    return [];
  }));
}

function StepProgress({ step }) {
  return <div className="mb-5 grid grid-cols-3 gap-2">{["Location", "Property details", "Analysis"].map((label, index) => { const number = index + 1; return <div key={label}><div className={`h-1 rounded-full ${number <= step ? "bg-slate-800" : "bg-slate-200"}`} /><p className={`mt-2 text-xs ${number === step ? "font-semibold text-slate-800" : "text-slate-400"}`}>{number}. {label}</p></div>; })}</div>;
}

export default function PredictForm() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    floor: "2.5", bedroom: "3", bathroom: "2", land_area: "", road_access: "12",
    property_age: "", has_parking: 0, has_balcony: 0, has_garden: 0,
    has_modular_kitchen: 0, location_encoded: "", facing_encoded: 2,
  });
  const [locations, setLocations] = useState([]);
  const [locationSearch, setLocationSearch] = useState("");
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [propertyPoint, setPropertyPoint] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => { axios.get("http://127.0.0.1:8000/locations").then((response) => setLocations(response.data)).catch(() => setLocations([])); }, []);
  const filteredLocations = useMemo(() => locations.filter((location) => location.label.toLowerCase().includes(locationSearch.toLowerCase())).sort((a, b) => a.label.localeCompare(b.label)).slice(0, 30), [locationSearch, locations]);
  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? (checked ? 1 : 0) : value }));
    if (fieldErrors[name]) setFieldErrors((current) => ({ ...current, [name]: undefined }));
  };

  const confirmLocation = (point) => {
    setPropertyPoint(point);
    if (!selectedLocation || !form.location_encoded) { setError("Select a recognised location from the suggestions before continuing."); return; }
    setError(""); setStep(2);
  };
  const submit = async (event) => {
    event.preventDefault();
    const validationErrors = validatePropertyForm(form);
    if (Object.keys(validationErrors).length) {
      setFieldErrors(validationErrors);
      setError("Review the highlighted property details before continuing.");
      return;
    }
    setFieldErrors({}); setLoading(true); setError("");
    try {
      const response = await axios.post("http://127.0.0.1:8000/predict", {
        floor: Number(form.floor), bedroom: Number(form.bedroom), bathroom: Number(form.bathroom),
        land_area: Number(form.land_area), road_access: Number(form.road_access), property_age: Number(form.property_age),
        has_parking: form.has_parking, has_balcony: form.has_balcony, has_garden: form.has_garden,
        has_modular_kitchen: form.has_modular_kitchen, location_encoded: Number(form.location_encoded),
        location_label: selectedLocation.label, facing_encoded: Number(form.facing_encoded),
      });
      setResult(response.data); setStep(3); window.scrollTo({ top: 0, behavior: "smooth" });
    } catch { setError("Property analysis failed. Review the entered details and try again."); }
    finally { setLoading(false); }
  };
  const restart = () => { setStep(1); setResult(null); setPropertyPoint(null); setError(""); };

  return <main className="mx-auto w-full max-w-[1380px] px-4 py-6">
    <div className="mb-6"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-700">Guided property analysis</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Understand a property and its location</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Follow three clear steps to estimate present property value and review current nearby infrastructure.</p></div>
    <StepProgress step={step} />

    {step === 1 && <section className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><span className="text-xs font-semibold text-blue-700">STEP 1</span><h2 className="mt-2 text-xl font-semibold text-slate-900">Where is the property located?</h2><p className="mt-2 text-sm leading-6 text-slate-500">Search for the recognised area, adjust the point on the map and confirm the exact location.</p>
        <div className="relative mt-6"><label className="text-xs font-semibold text-slate-600">Search location<input aria-label="Search location" value={locationSearch} onChange={(event) => { setLocationSearch(event.target.value); setSelectedLocation(null); setForm((current) => ({ ...current, location_encoded: "" })); setShowSuggestions(true); }} placeholder="e.g. Kalanki, Kathmandu" className={inputClass} /></label>{showSuggestions && locationSearch && <ul className="absolute z-[1000] mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg">{filteredLocations.length ? filteredLocations.map((location) => <li key={location.label}><button type="button" onClick={() => { setSelectedLocation(location); setLocationSearch(location.label); setForm((current) => ({ ...current, location_encoded: location.value })); setShowSuggestions(false); }} className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50">{location.label}</button></li>) : <li className="px-3 py-2 text-sm text-slate-400">No recognised locations found</li>}</ul>}</div>
        <div className="mt-5 rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-400">Recognised area</p><p className="mt-1 text-sm font-semibold text-slate-700">{selectedLocation?.label || "Select an area from the search results"}</p>{propertyPoint && <p className="mt-2 text-xs text-slate-500">Lat {propertyPoint.lat.toFixed(6)}, Lon {propertyPoint.lon.toFixed(6)}</p>}</div>
        <p className="mt-4 text-xs leading-5 text-slate-500">Selecting the exact property location improves the accuracy of nearby infrastructure analysis.</p>{error && <p role="alert" className="mt-3 text-sm text-red-600">{error}</p>}
      </div>
      <LocationMap locationLabel={selectedLocation?.label || locationSearch} onCoordinateChange={setPropertyPoint} onCoordinateConfirm={confirmLocation} stepNumber={null} />
    </section>}

    {step === 2 && <form onSubmit={submit} noValidate className="mx-auto max-w-4xl space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div><span className="text-xs font-semibold text-blue-700">STEP 2</span><h2 className="mt-2 text-xl font-semibold text-slate-900">Property information</h2><p className="mt-1 text-sm text-slate-500">Details for {selectedLocation?.label}.</p></div><button type="button" onClick={() => setStep(1)} className="text-xs font-semibold text-slate-500">Change location</button></div>
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <div className="rounded-xl bg-slate-50 p-4"><h3 className="text-sm font-semibold text-slate-800">Property size</h3><label className="mt-3 block text-xs font-medium text-slate-600">Land area in square feet<input aria-label="Land area" aria-invalid={Boolean(fieldErrors.land_area)} aria-describedby={fieldErrors.land_area ? "land_area-error" : undefined} type="number" min="102.675" max="5886.7" name="land_area" value={form.land_area} onChange={handleChange} placeholder="e.g. 1369" className={`${inputClass} ${fieldErrors.land_area ? "border-red-400 focus:border-red-500 focus:ring-red-100" : ""}`} /></label>{fieldErrors.land_area && <p id="land_area-error" className="mt-2 text-xs font-medium text-red-600">{fieldErrors.land_area}</p>}<p className="mt-2 text-xs text-slate-400">Supported range: 102.675–5,886.7 sq ft · 1 Aana ≈ 342.25 sq ft{form.land_area && Number(form.land_area) > 0 ? ` · approximately ${(Number(form.land_area) / 342.25).toFixed(2)} Aana` : ""}</p></div>
          <div className="rounded-xl bg-slate-50 p-4"><h3 className="text-sm font-semibold text-slate-800">Building</h3><div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">{[["bedroom", "Bedrooms"], ["bathroom", "Bathrooms"], ["floor", "Floors"]].map(([name, label]) => <label key={name} className="text-xs font-medium text-slate-600">{label}<input aria-label={label} aria-invalid={Boolean(fieldErrors[name])} aria-describedby={fieldErrors[name] ? `${name}-error` : undefined} type="number" min={FIELD_LIMITS[name].min} max={FIELD_LIMITS[name].max} step={name === "floor" ? "0.5" : "1"} name={name} value={form[name]} onChange={handleChange} className={`${inputClass} ${fieldErrors[name] ? "border-red-400 focus:border-red-500 focus:ring-red-100" : ""}`} />{fieldErrors[name] && <span id={`${name}-error`} className="mt-2 block text-xs font-medium text-red-600">{fieldErrors[name]}</span>}</label>)}</div></div>
          <div className="rounded-xl bg-slate-50 p-4"><h3 className="text-sm font-semibold text-slate-800">Accessibility and age</h3><div className="mt-3 grid grid-cols-2 gap-3"><label className="text-xs font-medium text-slate-600">Road access<select aria-label="Road access" name="road_access" value={form.road_access} onChange={handleChange} className={inputClass}>{ROAD_ACCESS_OPTIONS.map((value) => <option key={value} value={value}>{value} ft</option>)}</select></label><label className="text-xs font-medium text-slate-600">Property age<input aria-label="Property age" aria-invalid={Boolean(fieldErrors.property_age)} aria-describedby={fieldErrors.property_age ? "property_age-error" : undefined} type="number" min="0" max="100" name="property_age" value={form.property_age} onChange={handleChange} placeholder="Years" className={`${inputClass} ${fieldErrors.property_age ? "border-red-400 focus:border-red-500 focus:ring-red-100" : ""}`} />{fieldErrors.property_age && <span id="property_age-error" className="mt-2 block text-xs font-medium text-red-600">{fieldErrors.property_age}</span>}</label></div><label className="mt-3 block text-xs font-medium text-slate-600">Facing direction<select aria-label="Facing direction" name="facing_encoded" value={form.facing_encoded} onChange={handleChange} className={inputClass}>{FACING_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
          <div className="rounded-xl bg-slate-50 p-4"><h3 className="text-sm font-semibold text-slate-800">Amenities</h3><div className="mt-3 grid grid-cols-2 gap-3">{[["has_parking", "Parking"], ["has_balcony", "Balcony"], ["has_garden", "Garden"], ["has_modular_kitchen", "Modular kitchen"]].map(([name, label]) => <label key={name} className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" name={name} checked={form[name] === 1} onChange={handleChange} className="h-4 w-4 accent-slate-900" />{label}</label>)}</div></div>
        </div>
        {error && <div role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">{error}</div>}<button type="submit" disabled={loading} className="mt-6 w-full rounded-lg bg-slate-900 py-3 text-sm font-semibold text-white disabled:opacity-50">{loading ? "Analysing property..." : "Analyse Property"}</button>
      </section>
    </form>}

    {step === 3 && <div><div className="mb-4 flex items-center justify-between"><div><span className="text-xs font-semibold text-blue-700">STEP 3</span><h2 className="mt-1 text-xl font-semibold text-slate-900">Property analysis</h2></div><button type="button" onClick={restart} className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600">Start new analysis</button></div><PredictionDashboard result={result} form={form} locationLabel={selectedLocation?.label} propertyPoint={propertyPoint} /></div>}
  </main>;
}
