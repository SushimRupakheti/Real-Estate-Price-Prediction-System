import { useEffect, useState } from "react";
import { adjustPrice } from "../../services/macroApi";

const LABELS = {
  cpi_inflation: "CPI Inflation",
  housing_inflation: "Housing & Utilities CPI Inflation",
  lending_rate: "Weighted Average Lending Rate",
  deposit_rate: "Weighted Average Deposit Rate",
  credit_growth: "Private-Sector Credit Growth",
  remittance_growth: "Remittance Growth",
};
const formatMoney = (value) => `NPR ${Math.round(value || 0).toLocaleString("en-IN")}`;

function Badge({ status }) {
  const color = status === "Positive Market"
    ? "bg-emerald-100 text-emerald-800"
    : status === "Cooling Market"
      ? "bg-amber-100 text-amber-800"
      : "bg-slate-100 text-slate-700";
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${color}`}>{status}</span>;
}

export default function MacroConditionsCard({ result }) {
  const [macro, setMacro] = useState(result?.macro_adjustment || null);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState("");

  useEffect(() => setMacro(result?.macro_adjustment || null), [result]);

  const retry = async () => {
    setRetrying(true);
    setRetryError("");
    try {
      setMacro(await adjustPrice(result?.base_price || result?.predicted_price));
    } catch {
      setRetryError("No validated macroeconomic record could be loaded.");
    } finally {
      setRetrying(false);
    }
  };

  if (!macro) {
    return <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
      <h3 className="font-semibold text-slate-900">Short-Term Market Conditions</h3>
      <p className="mt-1 text-xs font-medium text-slate-500">Nepal Rastra Bank</p>
      <p className="mt-3 text-sm leading-6 text-amber-900">The current NRB macroeconomic adjustment is temporarily unavailable. The base machine-learning estimate is still shown.</p>
      <button type="button" onClick={retry} disabled={retrying} className="mt-3 rounded-lg border border-amber-300 bg-white px-3 py-2 text-xs font-semibold text-amber-900 disabled:opacity-50">{retrying ? "Loading..." : "Retry market data"}</button>
      {retryError && <p role="alert" className="mt-2 text-xs text-red-700">{retryError}</p>}
    </section>;
  }

  return <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 className="text-base font-semibold text-slate-900">Short-Term Market Conditions</h3>
        <p className="mt-1 text-xs text-slate-500">Nepal Rastra Bank · {macro.reference_period}</p>
        <p className="mt-2 inline-flex rounded-full bg-indigo-50 px-3 py-1 text-[11px] font-semibold text-indigo-700">Indicative 3–6 month macro outlook</p>
      </div>
      <div className="flex gap-2">
        <Badge status={macro.market_status} />
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${macro.data_status === "stale" ? "bg-amber-100 text-amber-800" : "bg-blue-50 text-blue-700"}`}>{macro.data_status}</span>
      </div>
    </div>

    {macro.data_status === "stale" && <p className="mt-3 rounded-lg bg-amber-50 p-3 text-xs text-amber-800">The latest validated record is older than the configured freshness threshold. Its period is shown for transparency.</p>}

    <div className="mt-5 grid gap-3 md:grid-cols-2">
      {macro.indicator_contributions.map((contribution) => <div key={contribution.indicator} className="rounded-xl bg-slate-50 p-3" title={contribution.measurement_basis || contribution.explanation}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold text-slate-700">{LABELS[contribution.indicator] || contribution.display_name}</p>
            <p className="mt-1 text-[11px] leading-4 text-slate-500">{contribution.measurement_basis || "Unavailable"}</p>
          </div>
          <div className="text-right">
            <p className="font-bold text-slate-900">{contribution.value == null ? "Unavailable" : `${contribution.value.toFixed(2)}%`}</p>
            {contribution.available && <p className={`text-[10px] font-semibold ${contribution.market_effect === "positive" ? "text-emerald-700" : contribution.market_effect === "negative" ? "text-amber-700" : "text-slate-500"}`}>{contribution.market_effect}</p>}
          </div>
        </div>
      </div>)}
    </div>

    <div className="mt-5 rounded-xl border border-blue-100 bg-blue-50 p-5">
      <div className="grid items-center gap-3 text-center sm:grid-cols-[1fr_auto_1fr_auto_1fr]">
        <div><p className="text-xs text-slate-500">Base ML Prediction</p><p className="mt-1 font-bold">{formatMoney(macro.base_price)}</p></div>
        <span>→</span>
        <div><p className="text-xs text-slate-500">Economic Adjustment</p><p className="mt-1 font-bold text-blue-700">{macro.adjustment_percentage >= 0 ? "+" : ""}{macro.adjustment_percentage.toFixed(2)}%</p></div>
        <span>→</span>
        <div><p className="text-xs text-slate-500">Indicative Value in 3–6 Months</p><p className="mt-1 font-bold text-blue-900">{formatMoney(macro.adjusted_price)}</p></div>
      </div>
      <p className="mt-4 text-xs leading-5 text-slate-600">The base machine-learning prediction remains unchanged. The indicative value applies a separate market-condition adjustment using the latest validated official macroeconomic indicators.</p>
    </div>

    <details className="mt-4 rounded-xl border border-slate-200 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-slate-700">Why was this adjustment applied?</summary>
      <p className="mt-3 text-sm leading-6 text-slate-600">{macro.economic_summary}</p>
      <div className="mt-3 space-y-2">
        {macro.indicator_contributions.filter((contribution) => contribution.available).map((contribution) => <p key={contribution.indicator} className="text-xs text-slate-600"><strong>{contribution.display_name}:</strong> baseline {contribution.baseline.toFixed(2)}%, contribution {contribution.contribution_percentage_points >= 0 ? "+" : ""}{contribution.contribution_percentage_points.toFixed(2)} pp. {contribution.explanation}</p>)}
      </div>
    </details>

    <p className="mt-4 text-xs leading-5 text-slate-500">Published {macro.publication_date}. <a href={macro.source_url} target="_blank" rel="noreferrer" className="font-semibold text-blue-700 underline">Official source</a>. The 3–6 month horizon is a project-defined interpretation of the current monthly indicators. It is not a statistically validated inflation or property-price forecast. Method: {macro.method === "documented_rule_assumptions" ? "documented rule-based assumptions" : macro.method}; not empirically calibrated.</p>
  </section>;
}
