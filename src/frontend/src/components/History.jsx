import { useEffect, useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line,
  ScatterChart, Scatter, ZAxis
} from "recharts";

const PAGE_SIZE = 15;

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/history")
      .then((res) => setHistory(res.data))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [history.length]);

  if (loading) return <p className="text-gray-500">Loading...</p>;

  if (history.length === 0) return (
    <div className="bg-white rounded-2xl shadow p-10 text-center text-gray-400">
      <div className="text-5xl mb-3">📭</div>
      <p>No predictions yet. Go to Predict tab to get started.</p>
    </div>
  );

  // Prepare chart data
  const priceChartData = history.map((item, i) => ({
    name: `#${item.id}`,
    price: Math.round(item.predicted_price / 100000),
  }));

  const bedroomChartData = history.map((item) => ({
    bedroom: item.bedroom,
    price: Math.round(item.predicted_price / 100000),
  }));

  const areaChartData = history.map((item) => ({
    area: Math.round(item.land_area),
    price: Math.round(item.predicted_price / 100000),
  }));

  const avgPrice = Math.round(
    history.reduce((s, i) => s + i.predicted_price, 0) / history.length
  );
  const maxPrice = Math.max(...history.map((i) => i.predicted_price));
  const minPrice = Math.min(...history.map((i) => i.predicted_price));
  const totalPages = Math.max(1, Math.ceil(history.length / PAGE_SIZE));
  const paginatedHistory = history.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Prediction History</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl shadow p-5 text-center">
          <p className="text-sm text-gray-500 mb-1">Total Predictions</p>
          <p className="text-4xl font-bold text-blue-600">{history.length}</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-5 text-center">
          <p className="text-sm text-gray-500 mb-1">Average Price</p>
          <p className="text-2xl font-bold text-green-600">
            ₹ {avgPrice.toLocaleString("en-IN")} L
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow p-5 text-center">
          <p className="text-sm text-gray-500 mb-1">Price Range</p>
          <p className="text-lg font-bold text-orange-500">
            {(minPrice / 10000000).toFixed(2)} Cr — {(maxPrice / 10000000).toFixed(2)} Cr
          </p>
        </div>
      </div>

      {/* Price Trend Chart */}
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-gray-700 mb-1">Price Trend</h3>
        <p className="text-xs text-gray-400 mb-4">
          Predicted prices across your recent predictions (in Lakhs)
        </p>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={priceChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis
              tickFormatter={(v) => `${v}L`}
              tick={{ fontSize: 11 }}
            />
            <Tooltip formatter={(v) => [`₹ ${v} Lakhs`, "Predicted Price"]} />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#1d4ed8"
              strokeWidth={2}
              dot={{ fill: "#1d4ed8", r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Bedroom vs Price Chart */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-semibold text-gray-700 mb-1">Bedrooms vs Price</h3>
          <p className="text-xs text-gray-400 mb-4">How bedroom count affects predicted price</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={bedroomChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bedroom" label={{ value: "Bedrooms", position: "insideBottom", offset: -2, fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `${v}L`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`₹ ${v} Lakhs`, "Price"]} />
              <Bar dataKey="price" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-semibold text-gray-700 mb-1">Land Area vs Price</h3>
          <p className="text-xs text-gray-400 mb-4">How land area affects predicted price</p>
          <ResponsiveContainer width="100%" height={220}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="area"
                name="Area"
                label={{ value: "sqft", position: "insideBottom", offset: -2, fontSize: 11 }}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                dataKey="price"
                name="Price"
                tickFormatter={(v) => `${v}L`}
                tick={{ fontSize: 11 }}
              />
              <ZAxis range={[40, 40]} />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                formatter={(v, name) => [
                  name === "Price" ? `₹ ${v} Lakhs` : `${v} sqft`,
                  name,
                ]}
              />
              <Scatter data={areaChartData} fill="#1d4ed8" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* History Table */}
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
            {paginatedHistory.map((item, index) => (
              <tr key={item.id} className={index % 2 === 0 ? "bg-gray-50" : "bg-white"}>
                <td className="px-4 py-3">{item.id}</td>
                <td className="px-4 py-3">{item.location_label || "-"}</td>
                <td className="px-4 py-3">{item.bedroom}</td>
                <td className="px-4 py-3">{item.bathroom}</td>
                <td className="px-4 py-3">{item.floor}</td>
                <td className="px-4 py-3">{item.land_area} sqft</td>
                <td className="px-4 py-3 font-semibold text-green-600">
                  ₹ {Math.round(item.predicted_price).toLocaleString("en-IN")}
                </td>
                <td className="px-4 py-3 text-gray-400">
                  {new Date(item.created_at).toLocaleDateString("en-IN")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between gap-3 px-4 py-3 border-t border-gray-100 bg-white">
          <p className="text-sm text-gray-500">
            Showing {(currentPage - 1) * PAGE_SIZE + 1}-{Math.min(currentPage * PAGE_SIZE, history.length)} of {history.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="text-sm font-medium text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}