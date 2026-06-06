import { useEffect, useState } from "react";
import axios from "axios";

export default function ModelStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/stats")
      .then((res) => setStats(res.data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!stats) return <p className="text-red-500">Failed to load stats.</p>;

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Model Performance</h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-sm text-gray-500 mb-1">R² Score</p>
          <p className="text-4xl font-bold text-blue-600">{stats.r2}</p>
          <p className="text-xs text-gray-400 mt-1">Higher is better</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-sm text-gray-500 mb-1">MAE</p>
          <p className="text-3xl font-bold text-orange-500">
            ₹ {stats.mae.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-gray-400 mt-1">Mean Absolute Error</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-sm text-gray-500 mb-1">RMSE</p>
          <p className="text-3xl font-bold text-red-500">
            ₹ {stats.rmse.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-gray-400 mt-1">Root Mean Square Error</p>
        </div>
      </div>

      {/* Model Info */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Model Details</h3>
        <div className="grid grid-cols-2 gap-4">
          {[
            { label: "Algorithm",        value: stats.model },
            { label: "Features Used",    value: stats.features },
            { label: "Training Samples", value: stats.train_size },
            { label: "Testing Samples",  value: stats.test_size },
          ].map((item) => (
            <div key={item.label} className="flex justify-between border-b pb-2">
              <span className="text-gray-500 text-sm">{item.label}</span>
              <span className="font-medium text-gray-800">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}