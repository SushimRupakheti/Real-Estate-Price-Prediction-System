import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import LocationMap from "./LocationMap";
import InfrastructureHealthIndex from "./InfrastructureHealthIndex";
import ScenarioSimulator from "./ScenarioSimulator";

const API_URL = "http://127.0.0.1:8000/infrastructure/analyze";
const CATEGORY_DEFS = [
  ["schools", "Schools"], ["colleges", "Colleges"], ["kindergartens", "Kindergartens"],
  ["hospitals", "Hospital-tagged places"], ["clinics", "Clinic-tagged places"],
  ["bus_stops", "Bus stops"], ["marketplaces", "Marketplaces"],
  ["supermarkets", "Supermarkets"], ["banks", "Bank-tagged places"], ["parks", "Park-tagged places"],
];
const distance = (value) => value == null ? "Unavailable" : value > 0 && value < 1 ? "<1 m" : `${Math.round(value).toLocaleString()} m`;

function RoadDetails({ title, road }) {
  return <div className="rounded-lg border border-gray-100 p-3"><p className="text-xs text-gray-500">{title}</p>{road ? <><p className="font-semibold text-gray-800 mt-1">{road.name}</p><p className="text-sm text-gray-600">{distance(road.distance_m)} · {road.highway_classification}</p><p className="text-xs text-gray-400">OSM {road.osm_type} {road.osm_id}</p></> : <p className="text-sm mt-1">Unavailable</p>}</div>;
}

function NearbyHighlights({ result }) {
  const items = [
    ["Nearest major road", result.roads.nearest_major_road ? `${distance(result.roads.nearest_major_road.distance_m)} · ${result.roads.nearest_major_road.highway_classification}` : "Unavailable"],
    ["Schools within 1 km", result.categories.schools.deduplicated_count],
    ["Hospital-tagged places within 2 km", result.categories.hospitals.deduplicated_count],
    ["Bus stops within 1 km", result.categories.bus_stops.deduplicated_count],
    ["Parks within 2 km", result.categories.parks.deduplicated_count],
  ];
  return <section className="rounded-2xl border border-cyan-200 border-l-4 border-l-cyan-600 bg-gradient-to-br from-white to-cyan-50/40 p-5 shadow-md shadow-cyan-900/5"><div className="flex items-start justify-between"><div><h3 className="text-sm font-semibold text-slate-900">Nearby Infrastructure Highlights</h3><p className="mt-1 text-xs text-slate-500">A concise view of current mapped infrastructure.</p></div><span className="rounded-full bg-cyan-100 px-2.5 py-1 text-[10px] font-semibold text-cyan-700">CURRENT AREA</span></div><div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">{items.map(([label, value]) => <div key={label} className="rounded-xl border border-cyan-100 bg-white/80 p-3 shadow-sm"><p className="text-[11px] leading-4 text-slate-500">{label}</p><p className="mt-2 text-base font-bold capitalize text-cyan-900">{value}</p></div>)}</div></section>;
}

function AssessmentSummary({ result }) {
  const counts = Object.fromEntries(Object.entries(result.categories).map(([key, value]) => [key, value.deduplicated_count]));
  const strengths = [];
  const considerations = [];
  if ((result.roads.nearest_major_road_distance_m ?? Infinity) <= 500) strengths.push("Strong access to the mapped major-road network.");
  else considerations.push("The nearest mapped major road is more than 500 m away.");
  if (counts.schools >= 5) strengths.push("Good mapped education availability within walking-area distance.");
  else considerations.push("Limited mapped schools were found within 1 km.");
  if (counts.hospitals + counts.clinics >= 3) strengths.push("Multiple healthcare-tagged places are mapped nearby.");
  else considerations.push("Few healthcare-tagged places are mapped within 2 km.");
  if (counts.bus_stops < 2) considerations.push("Mapped public-transport stops are limited within 1 km.");
  if (counts.supermarkets < 1) considerations.push("No mapped supermarket was found within 1 km.");
  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h3 className="text-sm font-semibold text-slate-900">Location Assessment Summary</h3><p className="mt-1 text-xs text-slate-500">Neutral observations from the current mapped indicators—not investment advice.</p><div className="mt-4 grid gap-3 md:grid-cols-2"><div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-4"><h4 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Strengths</h4><ul className="mt-2 space-y-2">{strengths.length ? strengths.map((item) => <li key={item} className="flex gap-2 text-xs leading-5 text-slate-700"><span className="font-bold text-emerald-600">✓</span>{item}</li>) : <li className="text-xs text-slate-500">No indicator crossed the configured summary thresholds.</li>}</ul></div><div className="rounded-xl border border-amber-100 bg-amber-50/60 p-4"><h4 className="text-xs font-semibold uppercase tracking-wide text-amber-700">Considerations</h4><ul className="mt-2 space-y-2">{considerations.map((item) => <li key={item} className="flex gap-2 text-xs leading-5 text-slate-700"><span className="font-bold text-amber-600">!</span>{item}</li>)}<li className="flex gap-2 text-xs leading-5 text-slate-700"><span className="font-bold text-amber-600">!</span>OpenStreetMap coverage and operating status may vary.</li></ul></div></div><div className="mt-4 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-500">The price is an ML estimate of present value. Infrastructure comes from OpenStreetMap and should not be interpreted as an investment recommendation.</div></section>;
}

function DataConfidence() {
  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h3 className="text-sm font-semibold text-slate-900">Data Confidence</h3><p className="mt-1 text-xs text-slate-500">Separate context indicators; they are not combined into one score.</p><div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{[["Price estimate", "Model-based"], ["Location accuracy", "Exact point confirmed"], ["Infrastructure coverage", "Coverage varies"], ["Scenario assumptions", "Illustrative"]].map(([label, value], index) => <div key={label} className={`rounded-lg border p-3 ${index < 2 ? "border-blue-100 bg-blue-50/50" : index === 2 ? "border-amber-100 bg-amber-50/50" : "border-violet-100 bg-violet-50/50"}`}><p className="text-[11px] text-slate-500">{label}</p><p className="mt-1 text-xs font-semibold text-slate-800">{value}</p></div>)}</div></section>;
}

export default function InfrastructureAnalysis({
  locationLabel,
  baselinePrice,
  pointOverride = null,
  hideMap = false,
  onMapFacilitiesChange,
  onFacilityFocusChange,
  autoAnalyze = false,
}) {
  const [point, setPoint] = useState(null); const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const [selectedFacility, setSelectedFacility] = useState(null); const [showAll, setShowAll] = useState(false);
  const [indexResult, setIndexResult] = useState(null);
  const autoStarted = useRef(false);
  const facilities = useMemo(() => {
    if (!result?.categories) return [];
    return CATEGORY_DEFS.flatMap(([key, label]) => (result.categories[key]?.places || []).map((place) => ({ ...place, category: key, category_label: label })));
  }, [result]);
  const mapFacilities = useMemo(
    () => showAll ? facilities : CATEGORY_DEFS.flatMap(([key]) => facilities.filter((place) => place.category === key).slice(0, 5)),
    [facilities, showAll],
  );

  useEffect(() => {
    if (pointOverride) setPoint(pointOverride);
  }, [pointOverride]);

  useEffect(() => {
    onMapFacilitiesChange?.(mapFacilities);
  }, [mapFacilities, onMapFacilitiesChange]);

  const selectFacility = (facility) => {
    setSelectedFacility(facility);
    onFacilityFocusChange?.(facility);
  };

  const handleIndexCalculated = useCallback((index) => {
    setIndexResult(index);
    if (!result || !baselinePrice) return;
    const record = {
      id: `${result.selected_location.latitude}:${result.selected_location.longitude}`,
      location: locationLabel || "Selected location",
      latitude: result.selected_location.latitude,
      longitude: result.selected_location.longitude,
      current_price: baselinePrice,
      overall_score: index.overall_score,
      classification: index.classification,
      category_scores: Object.fromEntries(Object.entries(index.categories).map(([key, value]) => [key, value.score])),
      indicators: index.indicators_used,
      analysed_at: new Date().toISOString(),
    };
    try {
      const existing = JSON.parse(localStorage.getItem("propertyAnalyses") || "[]");
      localStorage.setItem("propertyAnalyses", JSON.stringify([record, ...existing.filter((item) => item.id !== record.id)].slice(0, 20)));
    } catch {}
  }, [baselinePrice, locationLabel, result]);

  const analyze = useCallback(async () => {
    if (!point) return; setLoading(true); setError(""); setResult(null); setIndexResult(null); setSelectedFacility(null);
    try { const response = await axios.post(API_URL, { latitude: point.lat, longitude: point.lon, location_name: locationLabel || null }); setResult(response.data); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Infrastructure analysis is currently unavailable."); }
    finally { setLoading(false); }
  }, [locationLabel, point]);
  useEffect(() => {
    if (autoAnalyze && point && !autoStarted.current) { autoStarted.current = true; analyze(); }
  }, [analyze, autoAnalyze, point]);
  const exportJson = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob); const link = document.createElement("a");
    link.href = url; link.download = `infrastructure-${result.selected_location.latitude}-${result.selected_location.longitude}.json`;
    link.click(); URL.revokeObjectURL(url);
  };

  return <div className="space-y-3">
    {!hideMap && <LocationMap locationLabel={locationLabel} onCoordinateChange={setPoint} onCoordinateConfirm={setPoint} facilities={mapFacilities} selectedFacility={selectedFacility} onFacilitySelect={selectFacility} />}
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-semibold text-slate-800">Nearby Infrastructure</h3><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${loading ? "bg-blue-100 text-blue-700" : result ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{loading ? "Reviewing" : result ? "Ready" : "Waiting"}</span></div>
            <p className="mt-1 text-xs leading-5 text-slate-500">Current mapped roads and facilities around the confirmed property point.</p>
          </div>
        </div>
        <button type="button" disabled={!point || loading} onClick={analyze} className="shrink-0 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800 disabled:opacity-50">{loading ? "Reviewing nearby infrastructure..." : result ? "Refresh Nearby Infrastructure" : "Review Nearby Infrastructure"}</button>
      </div>
    </section>
    {!point && <p className="text-xs text-amber-700">Waiting for the map location. You can also click the map and confirm the property point.</p>}
    {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4"><p className="text-sm font-semibold text-red-700">{error}</p><p className="mt-1 text-xs leading-5 text-red-600">Your property-value estimate is still available. The OpenStreetMap provider may be busy; use Review Nearby Infrastructure to try again.</p></div>}
    {result && <NearbyHighlights result={result} />}
    {result && <InfrastructureHealthIndex analysis={result} onIndexCalculated={handleIndexCalculated} />}
    {result && <AssessmentSummary result={result} />}
    {result && <DataConfidence />}
    {result && <details className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><summary className="cursor-pointer text-sm font-semibold text-slate-700">Nearby mapped facilities and technical details</summary><div className="mt-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold text-gray-800">Current nearby infrastructure</h3><div className="flex gap-2"><button type="button" onClick={() => setShowAll((value) => !value)} className="text-xs border rounded-lg px-3 py-2">{showAll ? "Show nearest markers" : "Show all markers"}</button><button type="button" onClick={exportJson} className="text-xs bg-slate-700 text-white rounded-lg px-3 py-2">Export JSON</button></div></div>
      <div className="mt-3 grid sm:grid-cols-2 gap-2"><RoadDetails title="Nearest road" road={result.roads.nearest_road} /><RoadDetails title="Nearest major road" road={result.roads.nearest_major_road} /></div>
      <div className="mt-4 grid sm:grid-cols-2 gap-3">{CATEGORY_DEFS.map(([key, label]) => { const category = result.categories[key]; return <details key={key} className="border rounded-lg p-3"><summary className="cursor-pointer font-medium text-sm">{label} ({category.deduplicated_count})</summary><p className="text-xs text-gray-400 mt-1">{category.raw_count} raw OSM elements · {category.radius_m.toLocaleString()} m radius</p><div className="mt-2 space-y-1 max-h-64 overflow-y-auto">{category.places.length ? category.places.map((place) => <button type="button" key={`${place.osm_type}-${place.osm_id}`} onClick={() => selectFacility({ ...place, category: key, category_label: label })} className="w-full text-left rounded p-2 hover:bg-blue-50"><span className="block text-sm font-medium">{place.name}</span><span className="text-xs text-gray-500">{distance(place.distance_m)} · OSM {place.osm_type} {place.osm_id}</span></button>) : <p className="text-xs text-gray-500">No mapped places found.</p>}</div></details>; })}</div>
      <p className="text-xs text-gray-500 mt-4">Mapped places are deduplicated OpenStreetMap features, not verified operating facilities. Source: OpenStreetMap contributors.</p>
    </div></details>}
    {result && indexResult && baselinePrice && <ScenarioSimulator baselinePrice={baselinePrice} currentIndex={indexResult} />}
  </div>;
}
