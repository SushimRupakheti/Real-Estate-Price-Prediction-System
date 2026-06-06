import { useEffect, useState } from "react";
import axios from "axios";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/history")
      .then((res) => setHistory(res.data))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

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