import { useEffect, useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from "recharts";

const FRIENDLY_NAMES = {
  "LOCATION_ENCODED": "Location",
  "LAND AREA (sqft)": "Land Area",
  "BATHROOM": "Bathrooms",
  "BEDROOM": "Bedrooms",
  "FLOOR": "Floor",
  "ROAD ACCESS (ft)": "Road Access",
  "PROPERTY AGE": "Property Age",
  "AREA_PER_BEDROOM": "Area per Bedroom",
  "TOTAL_ROOMS": "Total Rooms",
  "FACING_ENCODED": "Facing Direction",
  "HAS_PARKING": "Parking",
  "HAS_BALCONY": "Balcony",
  "HAS_GARDEN": "Garden",
  "HAS_MODULAR_KITCHEN": "Modular Kitchen",
  "IS_NEW": "New Property",
};

const COLORS = [
  "#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa",
  "#93c5fd", "#bfdbfe", "#dbeafe", "#eff6ff",
];

export default function ModelStats() {
  const [stats, setStats] = useState(null);
  const [importance, setImportance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.allSettled([
      axios.get("http://127.0.0.1:8000/stats"),
      axios.get("http://127.0.0.1:8000/shap-importance"),
    ]).then(([statsResult, shapResult]) => {
      if (statsResult.status === "fulfilled") {
        setStats(statsResult.value.data);
      } else {
        setError("Model statistics are unavailable. Check that the FastAPI backend is running on port 8000.");
      }

      if (shapResult.status === "fulfilled") {
        setImportance(
          shapResult.value.data
          .filter((d) => d.importance > 0)
          .map((d) => ({
            ...d,
            label: FRIENDLY_NAMES[d.feature] || d.feature,
          }))
        );
      }
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500 p-8">Loading...</p>;
  if (!stats) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold">Unable to load model statistics</h2>
        <p className="mt-2 text-sm">{error}</p>
      </div>
    );
  }

  const modelComparison = stats.model_comparison || [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Model Performance</h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-sm text-gray-500 mb-1">R² Score</p>
          <p className="text-4xl font-bold text-blue-600">{stats.r2}</p>
          <p className="text-xs text-gray-400 mt-1">Higher is better (max 1.0)</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-sm text-gray-500 mb-1">MAE</p>
          <p className="text-2xl font-bold text-orange-500">
            ₹ {stats.mae.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-gray-400 mt-1">Mean Absolute Error</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-sm text-gray-500 mb-1">RMSE</p>
          <p className="text-2xl font-bold text-red-500">
            ₹ {stats.rmse.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-gray-400 mt-1">Root Mean Square Error</p>
        </div>
      </div>

      {/* Model Details */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Model Details</h3>
        <div className="grid grid-cols-2 gap-4">
          {[
            { label: "Algorithm", value: stats.model },
            { label: "Features Used", value: stats.features },
            { label: "Training Samples", value: stats.train_size },
            { label: "Testing Samples", value: stats.test_size },
          ].map((item) => (
            <div key={item.label} className="flex justify-between border-b pb-2">
              <span className="text-gray-500 text-sm">{item.label}</span>
              <span className="font-medium text-gray-800">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* SHAP Feature Importance Chart */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-1">
          Global Feature Importance
        </h3>
        <p className="text-xs text-gray-400 mb-4">
          Based on SHAP values — shows which features influence price the most across all predictions
        </p>
        <ResponsiveContainer width="100%" height={450}>
          <BarChart
            data={importance}
            layout="vertical"
            margin={{ top: 0, right: 30, left: 120, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={(v) =>
                v >= 1000000
                  ? `${(v / 1000000).toFixed(1)}M`
                  : `${(v / 1000).toFixed(0)}K`
              }
              tick={{ fontSize: 11 }}
            />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fontSize: 12 }}
              width={115}
            />
            <Tooltip
              formatter={(value) => [
                `₹ ${value.toLocaleString("en-IN")}`,
                "Avg SHAP Impact",
              ]}
            />
            <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
              {importance.map((_, index) => (
                <Cell
                  key={index}
                  fill={COLORS[Math.min(index, COLORS.length - 1)]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Model Comparison Table */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">
          Model Comparison
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-blue-700 text-white">
              <tr>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">MAE</th>
                <th className="px-4 py-3">RMSE</th>
                <th className="px-4 py-3">R²</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {modelComparison.map((row, i) => (
                <tr key={row.model} className={i % 2 === 0 ? "bg-gray-50" : "bg-white"}>
                  <td className="px-4 py-3 font-medium">{row.model}</td>
                  <td className="px-4 py-3">₹ {Math.round(row.mae).toLocaleString("en-IN")}</td>
                  <td className="px-4 py-3">₹ {Math.round(row.rmse).toLocaleString("en-IN")}</td>
                  <td className="px-4 py-3">{Number(row.r2).toFixed(4)}</td>
                  <td className="px-4 py-3">
                    {row.status === "Selected" ? (
                      <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-semibold">
                        ✅ Selected
                      </span>
                    ) : (
                      <span className="bg-gray-100 text-gray-500 px-2 py-1 rounded-full text-xs">
                        Baseline
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
