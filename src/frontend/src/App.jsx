import { useCallback, useEffect, useState } from "react";
import PredictForm from "./components/PredictForm";
import History from "./components/History";
import ModelStats from "./components/ModelStats";
import ModelCard from "./components/ModelCard";
import CompareLocations from "./components/CompareLocations";

const NAV_ITEMS = [
  ["/analyze/location", "Analyse Property"],
  ["/compare", "Compare Locations"],
  ["/saved_estimates", "Saved Estimates"],
  ["/model-performance", "Model Performance"],
  ["/methodology", "Methodology"],
];

const LEGACY_PATHS = {
  "/": "/analyze/location",
  "/analyze": "/analyze/location",
  "/saved-estimates": "/saved_estimates",
  "/model_performace": "/model-performance",
};

const VALID_PATHS = new Set([
  "/analyze/location",
  "/analyze/property-details",
  "/analyze/results",
  "/compare",
  "/saved_estimates",
  "/model-performance",
  "/methodology",
]);

function cleanPath(pathname) {
  const path = pathname.length > 1 ? pathname.replace(/\/$/, "") : pathname;
  return LEGACY_PATHS[path] || (VALID_PATHS.has(path) ? path : "/analyze/location");
}

export default function App() {
  const [path, setPath] = useState(() => cleanPath(window.location.pathname));

  const navigate = useCallback((nextPath, { replace = false } = {}) => {
    const normalized = cleanPath(nextPath);
    window.history[replace ? "replaceState" : "pushState"]({}, "", normalized);
    setPath(normalized);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  useEffect(() => {
    const requestedPath = window.location.pathname;
    const normalized = cleanPath(requestedPath);
    if (requestedPath !== normalized) window.history.replaceState({}, "", normalized);
    const handlePopState = () => setPath(cleanPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const analysisStep = path === "/analyze/results" ? 3 : path === "/analyze/property-details" ? 2 : 1;
  const activeSection = path.startsWith("/analyze/") ? "/analyze/location" : path;

  return <div className="light-theme flex min-h-screen flex-col bg-[#f7f8fc] text-slate-900">
    <header className="sticky top-0 z-[2000] border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-3 px-5 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <a href="/analyze/location" onClick={(event) => { event.preventDefault(); navigate("/analyze/location"); }} className="flex items-center gap-3 text-left">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 text-sm font-black text-white shadow-lg shadow-violet-950/40">NP</span>
          <span><span className="block text-sm font-bold tracking-tight text-slate-900">Nepal Property Insight</span><span className="block text-[11px] text-slate-500">Data-led property intelligence</span></span>
        </a>
        <nav aria-label="Primary navigation" className="flex gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-slate-50 p-1">
          {NAV_ITEMS.map(([itemPath, label]) => <a key={itemPath} href={itemPath} onClick={(event) => { event.preventDefault(); navigate(itemPath); }} aria-current={activeSection === itemPath ? "page" : undefined} className={`whitespace-nowrap rounded-lg px-3.5 py-2 text-xs font-semibold transition ${activeSection === itemPath ? "bg-white text-violet-700 shadow-sm ring-1 ring-slate-200" : "text-slate-500 hover:bg-white hover:text-slate-800"}`}>{label}</a>)}
        </nav>
      </div>
    </header>

    <div className="flex-1">
      {path.startsWith("/analyze/") && <PredictForm step={analysisStep} onNavigate={navigate} />}
      {path === "/compare" && <CompareLocations />}
      {path === "/saved_estimates" && <div className="mx-auto max-w-6xl px-4 py-8"><History /></div>}
      {path === "/model-performance" && <div className="mx-auto max-w-6xl px-4 py-8"><ModelStats /></div>}
      {path === "/methodology" && <div className="mx-auto max-w-6xl px-4 py-8"><ModelCard /></div>}
    </div>

    <footer className="mt-10 border-t border-slate-200 bg-white/70"><div className="mx-auto flex max-w-7xl flex-col gap-2 px-6 py-5 text-xs leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between"><p>Model estimates and OpenStreetMap-derived context for research and exploratory analysis.</p><p>Not investment advice or a professional property valuation.</p></div></footer>
  </div>;
}
