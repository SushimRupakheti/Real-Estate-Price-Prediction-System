import { useState } from "react";
import PredictForm from "./components/PredictForm";
import History from "./components/History";
import ModelStats from "./components/ModelStats";
import ModelCard from "./components/ModelCard";
import CompareLocations from "./components/CompareLocations";

const PAGES = [
  ["predict", "Analyse Property"],
  ["compare", "Compare Locations"],
  ["history", "Saved Estimates"],
  ["stats", "Model Performance"],
  ["modelcard", "Methodology"],
];

export default function App() {
  const [activePage, setActivePage] = useState("predict");
  return <div className="min-h-screen bg-[#f5f7fb] text-slate-900">
    <header className="sticky top-0 z-[2000] border-b border-slate-200/80 bg-white/95 shadow-sm backdrop-blur">
      <div className="mx-auto flex max-w-[1480px] flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
        <button type="button" onClick={() => setActivePage("predict")} className="flex items-center gap-3 text-left">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-700 text-base font-bold text-white shadow-sm">NP</span>
          <span><span className="block text-sm font-bold tracking-tight text-slate-950">Nepal Property Insight</span><span className="block text-[11px] text-slate-500">Property value and location analysis</span></span>
        </button>
        <nav aria-label="Primary navigation" className="flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1">
          {PAGES.map(([page, label]) => <button key={page} type="button" onClick={() => setActivePage(page)} className={`whitespace-nowrap rounded-lg px-3.5 py-2 text-xs font-semibold transition ${activePage === page ? "bg-white text-blue-700 shadow-sm" : "text-slate-600 hover:bg-white/60 hover:text-slate-900"}`}>{label}</button>)}
        </nav>
      </div>
    </header>

    {activePage === "predict" && <PredictForm />}
    {activePage === "compare" && <CompareLocations />}
    {activePage === "history" && <div className="mx-auto max-w-6xl px-4 py-8"><History /></div>}
    {activePage === "stats" && <div className="mx-auto max-w-6xl px-4 py-8"><ModelStats /></div>}
    {activePage === "modelcard" && <div className="mx-auto max-w-6xl px-4 py-8"><ModelCard /></div>}

    <footer className="mt-12 border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-[1480px] flex-col gap-2 px-4 py-5 text-[11px] leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between"><p>Model estimates and OpenStreetMap-derived context for research and exploratory analysis.</p><p>Not investment advice or a professional property valuation.</p></div></footer>
  </div>;
}
