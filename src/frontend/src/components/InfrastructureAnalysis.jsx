import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import LocationMap from "./LocationMap";
import InfrastructureHealthIndex from "./InfrastructureHealthIndex";

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

export default function InfrastructureAnalysis({
  locationLabel,
  pointOverride = null,
  hideMap = false,
  onMapFacilitiesChange,
  onFacilityFocusChange,
}) {
  const [point, setPoint] = useState(null); const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const [selectedFacility, setSelectedFacility] = useState(null); const [showAll, setShowAll] = useState(false);
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

  const analyze = async () => {
    if (!point) return; setLoading(true); setError(""); setResult(null); setSelectedFacility(null);
    try { const response = await axios.post(API_URL, { latitude: point.lat, longitude: point.lon, location_name: locationLabel || null }); setResult(response.data); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Infrastructure analysis is currently unavailable."); }
    finally { setLoading(false); }
  };
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
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">4</span>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">Nearby infrastructure</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">Review OSM-mapped roads and facilities around the confirmed point.</p>
          </div>
        </div>
        <button type="button" disabled={!point || loading} onClick={analyze} className="shrink-0 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800 disabled:opacity-50">{loading ? "Analyzing current infrastructure..." : "Analyze Infrastructure"}</button>
      </div>
    </section>
    {!point && <p className="text-xs text-amber-700">Waiting for the map location. You can also click the map and confirm the property point.</p>}
    {error && <p role="alert" className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">{error}</p>}
    {result && <InfrastructureHealthIndex analysis={result} />}
    {result && <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold text-gray-800">Current nearby infrastructure</h3><div className="flex gap-2"><button type="button" onClick={() => setShowAll((value) => !value)} className="text-xs border rounded-lg px-3 py-2">{showAll ? "Show nearest markers" : "Show all markers"}</button><button type="button" onClick={exportJson} className="text-xs bg-slate-700 text-white rounded-lg px-3 py-2">Export JSON</button></div></div>
      <div className="mt-3 grid sm:grid-cols-2 gap-2"><RoadDetails title="Nearest road" road={result.roads.nearest_road} /><RoadDetails title="Nearest major road" road={result.roads.nearest_major_road} /></div>
      <div className="mt-4 grid sm:grid-cols-2 gap-3">{CATEGORY_DEFS.map(([key, label]) => { const category = result.categories[key]; return <details key={key} className="border rounded-lg p-3"><summary className="cursor-pointer font-medium text-sm">{label} ({category.deduplicated_count})</summary><p className="text-xs text-gray-400 mt-1">{category.raw_count} raw OSM elements · {category.radius_m.toLocaleString()} m radius</p><div className="mt-2 space-y-1 max-h-64 overflow-y-auto">{category.places.length ? category.places.map((place) => <button type="button" key={`${place.osm_type}-${place.osm_id}`} onClick={() => selectFacility({ ...place, category: key, category_label: label })} className="w-full text-left rounded p-2 hover:bg-blue-50"><span className="block text-sm font-medium">{place.name}</span><span className="text-xs text-gray-500">{distance(place.distance_m)} · OSM {place.osm_type} {place.osm_id}</span></button>) : <p className="text-xs text-gray-500">No mapped places found.</p>}</div></details>; })}</div>
      <p className="text-xs text-gray-500 mt-4">Counts are deduplicated OSM-mapped features, not verified operating facilities. Select a listed place to highlight it on the map. Source: OpenStreetMap contributors. This is not a score or price forecast.</p>
    </div>}
  </div>;
}
