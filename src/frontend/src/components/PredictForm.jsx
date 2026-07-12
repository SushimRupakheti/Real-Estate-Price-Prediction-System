import { useState, useEffect } from "react";
import axios from "axios";
import PredictionDashboard from "./PredictionDashboard";

const FACING_OPTIONS = [
    { label: "East", value: 2 },
    { label: "West", value: 7 },
    { label: "North", value: 3 },
    { label: "South", value: 6 },
    { label: "North-East", value: 4 },
    { label: "North-West", value: 5 },
    { label: "South-East", value: 0 },
    { label: "South-West", value: 1 },
];

const ROAD_ACCESS_OPTIONS = [10, 12, 15, 20, 24, 30, 40];
const HERO_IMAGE =
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1800&q=80";

export default function PredictForm() {
    const [form, setForm] = useState({
        floor: "2.5",
        bedroom: "3",
        bathroom: "2",
        land_area: "",
        road_access: "12",
        property_age: "",
        has_parking: 0,
        has_balcony: 0,
        has_garden: 0,
        has_modular_kitchen: 0,
        location_encoded: "",
        facing_encoded: 2,
    });

    const [locations, setLocations] = useState([]);
    const [locationSearch, setLocationSearch] = useState("");
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get("http://127.0.0.1:8000/locations")
            .then((res) => setLocations(res.data))
            .catch(() => setLocations([]));
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setForm({ ...form, [name]: type === "checkbox" ? (checked ? 1 : 0) : value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const payload = {
                floor: parseFloat(form.floor),
                bedroom: parseFloat(form.bedroom),
                bathroom: parseFloat(form.bathroom),
                land_area: parseFloat(form.land_area),
                road_access: parseFloat(form.road_access),
                property_age: parseFloat(form.property_age),
                has_parking: form.has_parking,
                has_balcony: form.has_balcony,
                has_garden: form.has_garden,
                has_modular_kitchen: form.has_modular_kitchen,
                location_encoded: parseFloat(form.location_encoded),
                location_label: selectedLocation?.label || locationSearch,
                facing_encoded: parseInt(form.facing_encoded),
            };
            const response = await axios.post("http://127.0.0.1:8000/predict", payload);
            setResult(response.data);
        } catch (err) {
            setError("Prediction failed. Please check your inputs.");
        } finally {
            setLoading(false);
        }
    };

    const filteredLocations = locations
        .filter((loc) => loc.label.toLowerCase().includes(locationSearch.toLowerCase()))
        .sort((a, b) => {
            const s = locationSearch.toLowerCase();
            const aL = a.label.toLowerCase();
            const bL = b.label.toLowerCase();
            if (aL === s) return -1;
            if (bL === s) return 1;
            if (aL.startsWith(s) && !bL.startsWith(s)) return -1;
            if (!aL.startsWith(s) && bL.startsWith(s)) return 1;
            return aL.localeCompare(bL);
        });

    return (
        <div className="mx-auto max-w-[1240px]">
            <div className="mx-3 mt-3 relative h-44 rounded-xl bg-cover bg-center overflow-hidden shadow-sm border border-blue-100" style={{ backgroundImage: `linear-gradient(90deg, rgba(248,250,252,0.98) 0%, rgba(248,250,252,0.9) 34%, rgba(248,250,252,0.12) 72%), url(${HERO_IMAGE})` }}>
                <div className="absolute inset-0 flex items-center px-9">
                    <div className="text-slate-900 max-w-md">
                        <h1 className="text-[34px] font-bold leading-tight">
                            Predict the Price of<br />Houses in Nepal 🏠
                        </h1>
                        <p className="text-slate-600 mt-3 text-sm leading-6">
                            Get an estimated price based on location, size, features and other important factors.
                        </p>
                    </div>
                </div>
            </div>

            <div className="px-3 py-3 grid grid-cols-[430px_minmax(0,1fr)] gap-4 items-start">
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 min-h-[560px]">
                    <h2 className="text-blue-700 font-semibold text-lg mb-5 flex items-center gap-2">
                        👤 Enter House Details
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="relative">
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">📍 Location</label>
                            <input
                                type="text"
                                placeholder="Search location..."
                                value={locationSearch}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setLocationSearch(val);
                                    setSelectedLocation(null);
                                    setForm((prev) => ({ ...prev, location_encoded: "" }));
                                    setShowSuggestions(true);
                                }}
                                required={!form.location_encoded}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            {showSuggestions && locationSearch && (
                                <ul className="absolute z-10 bg-white border border-gray-200 rounded-lg shadow-lg w-full max-h-44 overflow-y-auto mt-1">
                                    {filteredLocations.map((loc) => (
                                        <li
                                            key={loc.label}
                                            onClick={() => {
                                                setForm((prev) => ({ ...prev, location_encoded: loc.value }));
                                                setLocationSearch(loc.label);
                                                setSelectedLocation(loc);
                                                setShowSuggestions(false);
                                            }}
                                            className="px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm text-gray-700"
                                        >
                                            {loc.label}
                                        </li>
                                    ))}
                                    {filteredLocations.length === 0 && (
                                        <li className="px-4 py-2 text-sm text-gray-400">No locations found</li>
                                    )}
                                </ul>
                            )}
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">📐 Land Area (sq ft) 1 AANA = 3456 sq ft</label>
                            <input
                                type="number"
                                name="land_area"
                                value={form.land_area}
                                onChange={handleChange}
                                placeholder="e.g. 1500"
                                required
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">🛣️ Road Access (ft)</label>
                            <select
                                name="road_access"
                                value={form.road_access}
                                onChange={handleChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {ROAD_ACCESS_OPTIONS.map((v) => (
                                    <option key={v} value={v}>{v} ft</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">🧭 Facing</label>
                            <select
                                name="facing_encoded"
                                value={form.facing_encoded}
                                onChange={handleChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {FACING_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-3 gap-2">
                            {[
                                { label: "🏢 Floor", name: "floor", placeholder: "2.5" },
                                { label: "🛏 Bedroom", name: "bedroom", placeholder: "3" },
                                { label: "🚿 Bathroom", name: "bathroom", placeholder: "2" },
                            ].map((f) => (
                                <div key={f.name}>
                                    <label className="text-xs font-medium text-gray-500 block mb-1">{f.label}</label>
                                    <input
                                        type="number"
                                        name={f.name}
                                        value={form[f.name]}
                                        onChange={handleChange}
                                        placeholder={f.placeholder}
                                        required
                                        className="w-full border border-gray-200 rounded-lg px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            ))}
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">📅 Property Age (Years)</label>
                            <input
                                type="number"
                                name="property_age"
                                value={form.property_age}
                                onChange={handleChange}
                                placeholder="e.g. 10"
                                required
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-2 block">✨ Amenities</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { label: "🚗 Parking", name: "has_parking" },
                                    { label: "🏗 Balcony", name: "has_balcony" },
                                    { label: "🌿 Garden", name: "has_garden" },
                                    { label: "🍳 Modular Kitchen", name: "has_modular_kitchen" },
                                ].map((item) => (
                                    <label key={item.name} className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
                                        <input
                                            type="checkbox"
                                            name={item.name}
                                            checked={form[item.name] === 1}
                                            onChange={handleChange}
                                            className="w-4 h-4 accent-blue-600"
                                        />
                                        {item.label}
                                    </label>
                                ))}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || !form.location_encoded}
                            className="w-full bg-blue-700 text-white py-3.5 rounded-lg font-semibold hover:bg-blue-800 transition disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? "Predicting..." : "📈 Predict Price"}
                        </button>

                        {error && <p className="text-red-500 text-sm text-center">{error}</p>}
                    </form>
                </div>

                <div className="min-w-0">
                    <PredictionDashboard
                        result={result}
                        form={form}
                        locationLabel={selectedLocation?.label || locationSearch}
                    />
                </div>
            </div>
        </div>
    );
}
