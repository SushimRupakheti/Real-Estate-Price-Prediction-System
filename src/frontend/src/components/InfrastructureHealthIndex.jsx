import { useEffect, useState } from "react";
import axios from "axios";

const INDEX_URL = "http://127.0.0.1:8000/infrastructure/index";

const scoreTone = (score) => score >= 85
  ? { text: "text-emerald-300", bar: "from-emerald-500 to-teal-400", badge: "bg-emerald-500/10 text-emerald-300" }
  : score >= 70
    ? { text: "text-cyan-300", bar: "from-cyan-500 to-blue-400", badge: "bg-cyan-500/10 text-cyan-300" }
    : { text: "text-amber-300", bar: "from-amber-500 to-orange-400", badge: "bg-amber-500/10 text-amber-300" };

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
    <section className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0d1424] shadow-2xl shadow-black/15">
      <div className="flex flex-col gap-5 border-b border-white/[0.07] bg-gradient-to-r from-emerald-500/[0.06] to-transparent px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-lg text-emerald-300 ring-1 ring-emerald-400/15">⌁</span>
          <div>
            <h3 className="text-base font-semibold text-white">Infrastructure Health Index</h3>
            <p className="mt-1 text-xs leading-5 text-slate-400">A rule-based view of access, services and amenities around this property.</p>
          </div>
        </div>
        {index && <div className="text-left sm:text-right">
          <div className="flex items-baseline gap-1 sm:justify-end"><p className="text-4xl font-black tracking-tight text-emerald-300">{index.overall_score}</p><span className="text-xs font-medium text-slate-500">/100</span></div>
          <p className="mt-1 inline-block rounded-full bg-emerald-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-300">{index.classification}</p>
        </div>}
      </div>

      {loading && <div className="px-6 py-10 text-center text-sm text-slate-500">Calculating the rule-based index...</div>}
      {error && <p role="alert" className="m-6 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {index && <>
        <div className="px-6 pt-5"><div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]"><div className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_12px_rgba(52,211,153,.45)]" style={{ width: `${index.overall_score}%` }} /></div></div>
        <details open className="m-6 rounded-xl border border-white/[0.07] bg-black/10 p-4"><summary className="cursor-pointer text-sm font-semibold text-slate-200">Score breakdown <span className="ml-2 text-xs font-normal text-slate-500">How each category performed</span></summary><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Object.values(index.categories).map((category) => {
            const tone = scoreTone(category.score);
            return (
            <details key={category.key} className="group rounded-xl border border-white/[0.07] bg-[#111b2e] p-4 transition hover:border-white/[0.12]">
              <summary className="cursor-pointer list-none">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-200">{category.label}</p>
                  <p className={`text-base font-bold ${tone.text}`}>{category.score}<span className="ml-0.5 text-[10px] font-normal text-slate-600">/100</span></p>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                  <div className={`h-full rounded-full bg-gradient-to-r ${tone.bar}`} style={{ width: `${category.score}%` }} />
                </div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${tone.badge}`}>{category.classification}</span>
                  <span className="text-[10px] text-slate-500 group-open:hidden">Details +</span>
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
            </details>);
          })}
        </div></details>
        <div className="flex flex-col gap-2 border-t border-white/[0.06] bg-black/10 px-6 py-4 text-[11px] leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between"><p>Based on currently mapped OpenStreetMap infrastructure.</p><p>Rule set {index.metadata.rules_version} · Context only, not a property valuation.</p></div>
      </>}
    </section>
  );
}
