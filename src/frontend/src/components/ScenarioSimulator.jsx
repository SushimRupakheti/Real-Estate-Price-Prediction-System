import { useState } from "react";
import axios from "axios";

const SCENARIO_URL = "http://127.0.0.1:8000/scenarios/simulate";
const ROAD_HIERARCHY = ["residential", "tertiary", "secondary", "primary", "trunk", "motorway"];
const PROJECT_GROUPS = [
  ["Transportation", [
    ["new_bus_stop", "Planned bus stops", 5],
    ["major_road_distance", "Planned major-road connection", null],
    ["improved_road_access", "Planned local-road improvement", null],
    ["road_upgrade", "Planned road upgrade", null],
  ]],
  ["Healthcare", [["new_hospital", "Planned hospital", 1], ["new_clinic", "Planned clinics", 5]]],
  ["Education", [["new_school", "Planned schools", 5], ["new_college", "Planned college", 1], ["new_kindergarten", "Planned kindergartens", 5]]],
  ["Commercial", [["new_marketplace", "Planned marketplace", 1], ["new_supermarket", "Planned supermarket", 1], ["new_bank", "Planned bank locations", 5]]],
  ["Public amenities", [["new_park", "Planned public park", 1]]],
];
const PROJECTS = Object.fromEntries(PROJECT_GROUPS.flatMap(([, projects]) => projects.map(([type, label, maximum]) => [type, { label, maximum }])));
const IMPACT_MESSAGES = {
  accessibility: "Road accessibility improved under the selected plan.",
  education: "Access to education facilities increased.",
  healthcare: "Healthcare accessibility improved.",
  commerce: "Nearby commercial services increased.",
  public_transport: "Public transport accessibility improved.",
  recreation: "Access to public recreation space improved.",
};
const formatPrice = (value) => `NPR ${(value / 10000000).toFixed(2)} Crore`;
const signed = (value) => value > 0 ? `+${value}` : String(value);
const signedCurrency = (value) => `${value > 0 ? "+" : value < 0 ? "−" : ""}${Math.abs(Math.round(value)).toLocaleString("en-IN")}`;
const distanceLabel = (metres) => metres >= 1000 ? `Within ${metres / 1000} km` : `Within ${metres} m`;

export default function ScenarioSimulator({ baselinePrice, currentIndex }) {
  const [planningEnabled, setPlanningEnabled] = useState(false);
  const [projectType, setProjectType] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [distance, setDistance] = useState("");
  const [roadUpgrade, setRoadUpgrade] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const indicators = currentIndex.indicators_used;
  const currentRoadIndex = ROAD_HIERARCHY.indexOf(indicators.nearest_major_road_type);
  const upgradeOptions = currentRoadIndex >= 0 ? ROAD_HIERARCHY.slice(currentRoadIndex + 1) : [];
  const project = PROJECTS[projectType];
  const requiresDistance = projectType === "major_road_distance" || projectType === "improved_road_access";
  const currentDistance = projectType === "major_road_distance" ? indicators.nearest_major_road_distance_m : indicators.nearest_road_distance_m;
  const distanceOptions = requiresDistance && currentDistance != null
    ? (projectType === "major_road_distance" ? [100, 250, 500, 1000, 2000] : [5, 10, 25, 50, 100, 250, 500]).filter((value) => value < currentDistance)
    : [];
  const selectionReady = Boolean(projectType) && (!requiresDistance || distance !== "") && (projectType !== "road_upgrade" || roadUpgrade);

  const selectProject = (value) => {
    setProjectType(value); setQuantity(1); setDistance(""); setRoadUpgrade("");
    setResult(null); setError("");
  };
  const reset = () => {
    setPlanningEnabled(false); selectProject(""); setResult(null); setError("");
  };
  const selectedSummary = () => {
    if (!project) return "No planned development selected.";
    if (requiresDistance) return `${project.label}: estimated new distance ${distance || "not entered"} m`;
    if (projectType === "road_upgrade") return `${project.label}: ${indicators.nearest_major_road_type} to ${roadUpgrade || "not selected"}`;
    return project.maximum === 1 ? project.label : `${project.label}: ${quantity}`;
  };

  const evaluate = async () => {
    let change;
    if (requiresDistance) change = { type: projectType, new_distance_m: Number(distance) };
    else if (projectType === "road_upgrade") change = { type: projectType, new_road_type: roadUpgrade };
    else change = { type: projectType, quantity };
    setLoading(true); setError(""); setResult(null);
    try {
      const response = await axios.post(SCENARIO_URL, { baseline_price: baselinePrice, current_infrastructure: indicators, changes: [change] }, { timeout: 15000 });
      setResult(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Scenario analysis is currently unavailable.");
    } finally {
      setLoading(false);
    }
  };
  const positiveImpacts = result ? Object.entries(result.scenario.category_score_differences).filter(([, difference]) => difference > 0) : [];
  const minimumValueDifference = result ? result.value_shift.minimum_value - baselinePrice : 0;
  const maximumValueDifference = result ? result.value_shift.maximum_value - baselinePrice : 0;
  const hasValueIncrease = maximumValueDifference > 0;

  return <section className="overflow-hidden rounded-2xl border border-slate-700 bg-white shadow-sm">
    <div className="flex flex-col gap-3 border-b border-slate-800 bg-slate-50 p-5 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-sm font-bold text-white shadow-sm">F</span><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-base font-semibold text-slate-900">Future Infrastructure Planning</h3><span className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-semibold text-violet-700">OPTIONAL</span></div><p className="mt-1 max-w-2xl text-xs leading-5 text-slate-500">Evaluate one announced, proposed, or hypothetical development at a time without changing current infrastructure data.</p></div></div>
      <div className="text-left sm:text-right"><p className="text-xs text-slate-400">Current property assessment</p><p className="text-sm font-semibold text-slate-800">{formatPrice(baselinePrice)}</p><p className="mt-1 text-xs text-slate-500">Current IHI: {currentIndex.overall_score}/100</p></div>
    </div>

    <div className="p-5"><aside className="rounded-xl border border-violet-900/60 bg-violet-950/20 p-4"><h4 className="text-sm font-semibold text-violet-300">About this scenario</h4><p className="mt-1 text-xs leading-5 text-slate-500">Use this only when exploring a planned or proposed government or private-sector project. The analysis does not predict whether the project will be approved, funded, or completed.</p></aside>

    <label className="mt-5 flex cursor-pointer items-start justify-between gap-4 rounded-xl border border-slate-700 bg-slate-50 p-4 transition hover:border-violet-700"><span><span className="block text-sm font-semibold text-slate-800">Evaluate a planned or proposed project</span><span className="mt-1 block text-xs leading-5 text-slate-500">Enable this only when you want to explore a specific future development.</span></span><input aria-label="Enable future scenario" type="checkbox" checked={planningEnabled} onChange={(event) => { setPlanningEnabled(event.target.checked); if (!event.target.checked) selectProject(""); }} className="mt-1 h-5 w-5 shrink-0 accent-violet-600" /></label>

    {planningEnabled && <div className="mt-4 rounded-xl border border-slate-700 bg-slate-950/30 p-4">
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-xs font-medium text-slate-600">Planned development<select aria-label="Planned development" value={projectType} onChange={(event) => selectProject(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700"><option value="">Select a proposed project</option>{PROJECT_GROUPS.map(([group, projects]) => <optgroup key={group} label={group}>{projects.map(([type, label]) => <option key={type} value={type}>{label}</option>)}</optgroup>)}</select></label>

        {project?.maximum > 1 && <label className="text-xs font-medium text-slate-600">Number included in the proposal<select aria-label="Planned project quantity" value={quantity} onChange={(event) => setQuantity(Number(event.target.value))} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700">{Array.from({ length: project.maximum }, (_, index) => index + 1).map((value) => <option key={value} value={value}>{value}</option>)}</select></label>}

        {requiresDistance && <label className="text-xs font-medium text-slate-600">Planned accessibility<span className="mt-1 block text-[10px] font-normal leading-4 text-slate-400">Choose the expected proximity after completion. Current mapped distance: {currentDistance ?? "Unavailable"} m.</span>{distanceOptions.length ? <select aria-label="Planned accessibility" value={distance} onChange={(event) => setDistance(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700"><option value="">Select expected proximity</option>{distanceOptions.map((value) => <option key={value} value={value}>{distanceLabel(value)}</option>)}</select> : <span className="mt-2 block rounded-lg bg-slate-50 p-3 text-xs font-normal text-slate-500">No closer preset is available because current mapped access is already within the smallest configured band.</span>}</label>}

        {projectType === "road_upgrade" && <label className="text-xs font-medium text-slate-600">Future road classification<span className="mt-1 block text-[10px] font-normal leading-4 text-slate-400">Current classification: {indicators.nearest_major_road_type || "Unavailable"}.</span><select aria-label="Future road classification" value={roadUpgrade} onChange={(event) => setRoadUpgrade(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="">Select the proposed classification</option>{upgradeOptions.map((roadType) => <option key={roadType} value={roadType}>{roadType}</option>)}</select></label>}
      </div>

      <div className="mt-4 rounded-lg bg-slate-50 p-3"><p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Selected future development</p><p className="mt-1 text-xs font-medium text-slate-700">{selectedSummary()}</p></div>
      <div className="mt-4 flex flex-wrap gap-2"><button type="button" onClick={evaluate} disabled={loading || !selectionReady} className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-500 disabled:opacity-50">{loading ? "Evaluating future scenario..." : "Evaluate Future Scenario"}</button><button type="button" onClick={reset} className="rounded-lg border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-slate-800">Reset scenario</button></div>
    </div>}
    {error && <p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

    {result && <div className="mt-6 space-y-4 border-t border-violet-100 pt-5">
      <div className={`overflow-hidden rounded-2xl border p-5 text-white shadow-lg ${hasValueIncrease ? "scenario-increase border-emerald-700 bg-emerald-950/40 shadow-emerald-950/20 ring-1 ring-emerald-800/60" : "border-violet-700 bg-violet-950/50 shadow-violet-950/20 ring-1 ring-violet-800/60"}`}>
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-100">Illustrative scenario value impact</p><p className="mt-2 text-sm text-blue-100">Current estimated value</p><p className="mt-1 text-2xl font-bold">{result.baseline_price?.formatted || formatPrice(baselinePrice)}</p></div>
          <div className="hidden text-3xl text-blue-200 lg:block">→</div>
          <div className="lg:text-right"><p className="text-sm text-blue-100">Illustrative value range after selected development</p><p className="mt-1 text-2xl font-bold sm:text-3xl">{result.value_shift.minimum_value_formatted} – {result.value_shift.maximum_value_formatted}</p><div className="mt-3 flex flex-wrap gap-2 lg:justify-end"><span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">{signed(result.value_shift.minimum_percent)}% to {signed(result.value_shift.maximum_percent)}%</span><span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-blue-700">Difference: {signedCurrency(minimumValueDifference)} to {signedCurrency(maximumValueDifference)} NPR</span></div></div>
        </div>
        <p className="mt-4 border-t border-white/20 pt-3 text-[11px] leading-5 text-blue-100">This is a configurable rule-based illustration derived from the Infrastructure Health Index change. It is not a predicted selling price or guaranteed return.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr]"><div className="rounded-xl border border-slate-200 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Current situation</p><p className="mt-3 text-xs text-slate-500">Infrastructure Health Index</p><p className="mt-1 text-2xl font-bold text-slate-900">{result.current.overall_index}/100</p><p className="mt-3 text-xs text-slate-500">Current property assessment</p><p className="mt-1 text-sm font-semibold text-slate-800">{result.baseline_price?.formatted || formatPrice(baselinePrice)}</p></div><div className="flex items-center justify-center text-xl text-slate-300">→</div><div className="rounded-xl border border-slate-200 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Future scenario</p><p className="mt-3 text-xs text-slate-500">Infrastructure Health Index</p><p className="mt-1 text-2xl font-bold text-slate-900">{result.scenario.overall_index}/100 <span className="text-sm font-semibold text-slate-500">({signed(result.scenario.index_change)})</span></p><p className="mt-3 text-xs text-slate-500">Illustrative property-value assessment</p><p className="mt-1 text-sm font-semibold text-slate-800">{result.value_shift.minimum_value_formatted} – {result.value_shift.maximum_value_formatted}</p></div></div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">{Object.entries(result.current.category_scores).map(([key, currentScore]) => { const scenarioScore = result.scenario.category_scores[key]; return <div key={key} className="rounded-lg border border-slate-200 p-3"><div className="flex items-center justify-between text-xs"><span className="font-medium capitalize text-slate-700">{key.replace("_", " ")}</span><span className="font-semibold text-slate-800">{currentScore} → {scenarioScore}</span></div><div className="mt-2 h-1.5 rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-700" style={{ width: `${scenarioScore}%` }} /></div></div>; })}</div>
      <div className="rounded-xl border border-slate-200 p-4"><h4 className="text-sm font-semibold text-slate-800">Impact summary</h4>{positiveImpacts.length ? <ul className="mt-3 space-y-2">{positiveImpacts.map(([category]) => <li key={category} className="flex gap-2 text-xs text-slate-600"><span className="text-slate-400">•</span>{IMPACT_MESSAGES[category]}</li>)}{result.scenario.index_change > 0 && <li className="flex gap-2 text-xs font-medium text-slate-700"><span className="text-slate-400">•</span>Overall infrastructure quality increased under this scenario.</li>}</ul> : <p className="mt-2 text-xs text-slate-500">The selected development did not cross a configured Infrastructure Health Index threshold.</p>}</div>
      {result.rule_contributions.length > 0 && <details className="rounded-xl border border-slate-200 p-4"><summary className="cursor-pointer text-sm font-semibold text-slate-700">Review rule-based contributions</summary><div className="mt-3 space-y-2">{result.rule_contributions.map((item, index) => <div key={`${item.change_type}-${item.category}-${index}`} className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600"><p className="font-medium text-slate-700">{item.change}</p><p className="mt-1 capitalize">{item.category.replace("_", " ")}: {item.current_category_score} → {item.scenario_category_score} ({signed(item.score_difference)})</p></div>)}</div></details>}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900"><p>This scenario represents a proposed or hypothetical infrastructure development selected by the user. It is intended for planning and exploratory analysis only.</p><p className="mt-1">It is not a prediction that the project will occur, nor a guarantee of future property value.</p><p className="mt-1">{result.metadata.disclaimer}</p></div>
    </div>}
    </div>
  </section>;
}
