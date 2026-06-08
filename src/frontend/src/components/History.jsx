import { useEffect, useState } from "react";
import axios from "axios";

export default function History() {
  const [history, setHistory] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch both history and locations in parallel
    Promise.all([
      axios.get("http://127.0.0.1:8000/history").then((r) => r.data).catch(() => []),
      axios.get("http://127.0.0.1:8000/locations").then((r) => r.data).catch(() => []),
    ])
      .then(([historyData, locationsData]) => {
        setHistory(historyData);
        setLocations(locationsData);
      })
      .catch(() => {
        setHistory([]);
        setLocations([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const lookupLocationLabel = (encoded) => {
    if (!encoded || locations.length === 0) return null;
    const found = locations.find((l) => Number(l.value) === Number(encoded));
    return found ? found.label : null;
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Prediction History</h2>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : history.length === 0 ? (
        <div className="bg-white rounded-2xl shadow p-6 text-center text-gray-400">
          No predictions yet. Go to Predict tab to get started.
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-blue-700 text-white">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Bedrooms</th>
                <th className="px-4 py-3">Bathrooms</th>
                <th className="px-4 py-3">Floor</th>
                <th className="px-4 py-3">Land Area</th>
                <th className="px-4 py-3">Predicted Price</th>
                <th className="px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item, index) => (
                <tr key={item.id} className={index % 2 === 0 ? "bg-gray-50" : "bg-white"}>
                  <td className="px-4 py-3">{item.id}</td>
                  <td className="px-4 py-3">{item.location_label || lookupLocationLabel(item.location_encoded) || "N/A"}</td>
                  <td className="px-4 py-3">{item.bedroom}</td>
                  <td className="px-4 py-3">{item.bathroom}</td>
                  <td className="px-4 py-3">{item.floor}</td>
                  <td className="px-4 py-3">{item.land_area} sqft</td>
                  <td className="px-4 py-3 font-semibold text-green-600">
                    ₹ {item.predicted_price.toLocaleString("en-IN")}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(item.created_at).toLocaleDateString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}