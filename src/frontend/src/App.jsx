import { useState } from "react";
import PredictForm from "./components/PredictForm";
import History from "./components/History";
import ModelStats from "./components/ModelStats";

export default function App() {
  const [activePage, setActivePage] = useState("predict");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* NAVBAR */}
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-blue-700 text-xl">🏠</span>
          <span className="font-semibold text-gray-800">Nepal House Predictor</span>
        </div>
        <div className="flex gap-2">
          {["predict", "history", "stats"].map((page) => (
            <button
              key={page}
              onClick={() => setActivePage(page)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
                activePage === page
                  ? "bg-blue-700 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {page === "predict" ? "Predict" : page === "history" ? "History" : "Model Stats"}
            </button>
          ))}
        </div>
      </nav>

      {/* PAGE */}
      {activePage === "predict" && <PredictForm />}
      {activePage === "history" && (
        <div className="max-w-5xl mx-auto px-6 py-8"><History /></div>
      )}
      {activePage === "stats" && (
        <div className="max-w-5xl mx-auto px-6 py-8"><ModelStats /></div>
      )}

      {/* FOOTER */}
      <footer className="text-center text-sm text-gray-400 py-4 border-t mt-8">
        Made with ❤️ for better real estate decisions.
      </footer>
    </div>
  );
}