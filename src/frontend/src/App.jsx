import { useState } from "react";
import PredictForm from "./components/PredictForm";
import History from "./components/History";
import ModelStats from "./components/ModelStats";
import ModelCard from "./components/ModelCard";

export default function App() {
  const [activePage, setActivePage] = useState("predict");

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white/90 border-b border-gray-200 px-4 py-2 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-blue-700 text-xl">🏠</span>
          <span className="font-semibold text-gray-800">Nepal House Predictor</span>
        </div>

        <div className="flex gap-3">
          {["predict", "history", "stats", "modelcard"].map((page) => (
            <button
              key={page}
              onClick={() => setActivePage(page)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
                activePage === page
                  ? "bg-blue-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {page === "predict"
                ? "Predict"
                : page === "history"
                  ? "History"
                  : page === "stats"
                    ? "Model Stats"
                    : "Model Card"}
            </button>
          ))}
        </div>
      </nav>

      {activePage === "predict" && <PredictForm />}
      {activePage === "history" && (
        <div className="max-w-5xl mx-auto px-6 py-8"><History /></div>
      )}
      {activePage === "stats" && (
        <div className="max-w-5xl mx-auto px-6 py-8"><ModelStats /></div>
      )}
      {activePage === "modelcard" && (
        <div className="max-w-5xl mx-auto px-6 py-8">
          <ModelCard />
        </div>
      )}
    </div>
  );
}
