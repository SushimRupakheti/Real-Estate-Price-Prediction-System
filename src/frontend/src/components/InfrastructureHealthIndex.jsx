import { useEffect, useState } from "react";
import axios from "axios";

const INDEX_URL = "http://127.0.0.1:8000/infrastructure/index";

export default function InfrastructureHealthIndex({ analysis, onIndexCalculated }) {
  const [index, setIndex] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!analysis) return undefined;
    let active = true;
    setLoading(true);
    setError("");
    setIndex(null);
    axios.post(INDEX_URL, { analysis }, { timeout: 15000 })
      .then((response) => { if (active) { setIndex(response.data); onIndexCalculated?.(response.data); } })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || "Infrastructure Health Index is currently unavailable.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [analysis, onIndexCalculated]);

  return (
    <section className="rounded-2xl border border-emerald-200 border-l-4 border-l-emerald-600 bg-gradient-to-br from-white to-emerald-50/40 p-5 shadow-md shadow-emerald-900/5">
      <div className="flex flex-col gap-4 border-b border-blue-100 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Infrastructure Health Index</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">Overall infrastructure quality from current OSM-mapped indicators.</p>
          </div>
        </div>
        {index && <div className="text-left sm:text-right">
          <p className="text-3xl font-bold text-emerald-800">{index.overall_score}<span className="text-sm font-medium text-slate-400">/100</span></p>
          <p className="mt-1 inline-block rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">{index.classification}</p>
        </div>}
      </div>

      {loading && <div className="py-8 text-center text-sm text-slate-500">Calculating the rule-based index...</div>}
      {error && <p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {index && <>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-emerald-100"><div className="h-full rounded-full bg-emerald-600" style={{ width: `${index.overall_score}%` }} /></div>
        <details className="mt-5 rounded-xl border border-slate-200 p-4"><summary className="cursor-pointer text-sm font-semibold text-slate-700">Infrastructure Health Index explanation</summary><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Object.values(index.categories).map((category) => (
            <details key={category.key} className="group rounded-xl border border-slate-200 bg-white p-4">
              <summary className="cursor-pointer list-none">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-800">{category.label}</p>
                  <p className="text-sm font-bold text-slate-900">{category.score}</p>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-slate-700" style={{ width: `${category.score}%` }} />
                </div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-slate-500">{category.classification}</span>
                  <span className="text-[11px] text-slate-400 group-open:hidden">View explanation</span>
                </div>
              </summary>
              <div className="mt-4 border-t border-slate-100 pt-3">
                <p className="text-xs leading-5 text-slate-500">{category.description}</p>
                <div className="mt-3 space-y-3">
                  {category.rules_used.map((rule) => (
                    <div key={rule.indicator} className="rounded-lg bg-slate-50 p-3">
                      <div className="flex items-start justify-between gap-3 text-xs">
                        <span className="font-medium text-slate-700">{rule.label}</span>
                        <span className="shrink-0 font-semibold text-slate-800">{rule.display_value}</span>
                      </div>
                      <p className="mt-1 text-[11px] leading-4 text-slate-500">Matched: {rule.matched_rule}</p>
                      <p className="mt-1 text-[10px] text-slate-400">Component {rule.component_score} × weight {rule.component_weight} = {rule.weighted_contribution}</p>
                    </div>
                  ))}
                </div>
              </div>
            </details>
          ))}
        </div></details>
        <p className="mt-4 text-xs leading-5 text-slate-500">
          Rule set {index.metadata.rules_version}. This index describes current mapped infrastructure; it is not a future-price forecast or property valuation.
        </p>
      </>}
    </section>
  );
}
