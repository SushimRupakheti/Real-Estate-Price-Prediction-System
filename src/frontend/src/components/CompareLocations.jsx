import { useMemo, useState } from "react";

const ROWS = [
  ["Current estimated value", (item) => `NPR ${(item.current_price / 10000000).toFixed(2)} Crore`],
  ["Infrastructure Health Index", (item) => `${item.overall_score}/100 · ${item.classification}`],
  ["Accessibility", (item) => item.category_scores.accessibility],
  ["Education", (item) => item.category_scores.education],
  ["Healthcare", (item) => item.category_scores.healthcare],
  ["Commerce", (item) => item.category_scores.commerce],
  ["Public transport", (item) => item.category_scores.public_transport],
  ["Recreation", (item) => item.category_scores.recreation],
  ["Nearest major road", (item) => item.indicators.nearest_major_road_distance_m == null ? "Unavailable" : `${Math.round(item.indicators.nearest_major_road_distance_m)} m`],
  ["Schools within 1 km", (item) => item.indicators.schools],
  ["Hospital-tagged places within 2 km", (item) => item.indicators.hospitals],
  ["Bus stops within 1 km", (item) => item.indicators.bus_stops],
];

export default function CompareLocations() {
  const analyses = useMemo(() => { try { return JSON.parse(localStorage.getItem("propertyAnalyses") || "[]"); } catch { return []; } }, []);
  const [leftId, setLeftId] = useState(analyses[0]?.id || "");
  const [rightId, setRightId] = useState(analyses[1]?.id || "");
  const left = analyses.find((item) => item.id === leftId);
  const right = analyses.find((item) => item.id === rightId);
  return <main className="mx-auto max-w-6xl px-4 py-8"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-700">Current analyses only</p><h1 className="mt-2 text-3xl font-bold text-slate-950">Compare Locations</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Compare two completed property analyses using current price estimates and current mapped infrastructure. Future scenarios are excluded.</p>
    {analyses.length < 2 ? <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center"><h2 className="text-base font-semibold text-slate-800">Analyse at least two locations first</h2><p className="mt-2 text-sm text-slate-500">Completed analyses are saved in this browser for comparison.</p></div> : <>
      <div className="mt-6 grid gap-4 md:grid-cols-2">{[["Location A", leftId, setLeftId], ["Location B", rightId, setRightId]].map(([label, value, setter]) => <label key={label} className="rounded-xl border border-slate-200 bg-white p-4 text-xs font-semibold text-slate-600 shadow-sm">{label}<select aria-label={label} value={value} onChange={(event) => setter(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm font-normal text-slate-700">{analyses.map((item) => <option key={item.id} value={item.id}>{item.location}</option>)}</select></label>)}</div>
      {left && right && <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="grid grid-cols-[minmax(170px,1fr)_minmax(160px,1fr)_minmax(160px,1fr)] bg-slate-900 px-4 py-3 text-sm font-semibold text-white"><span>Measure</span><span>{left.location}</span><span>{right.location}</span></div>{ROWS.map(([label, read], index) => <div key={label} className={`grid grid-cols-[minmax(170px,1fr)_minmax(160px,1fr)_minmax(160px,1fr)] gap-3 px-4 py-3 text-sm ${index % 2 ? "bg-slate-50" : "bg-white"}`}><span className="font-medium text-slate-600">{label}</span><span className="text-slate-800">{read(left)}</span><span className="text-slate-800">{read(right)}</span></div>)}</div>}
      <p className="mt-4 text-xs leading-5 text-slate-500">Comparison values are model estimates and OpenStreetMap-derived indicators. They do not constitute investment advice.</p>
    </>}
  </main>;
}
