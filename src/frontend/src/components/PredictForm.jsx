import { useState, useEffect } from "react";
import axios from "axios";

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
            console.log("Location Encoded Being Sent:", form.location_encoded);
            console.log("Location Label:", locationSearch);
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
        <div>
            {/* HERO BANNER */}
            <div className="relative h-52 bg-gradient-to-r from-blue-900 to-blue-700 overflow-hidden">
                <div className="absolute inset-0 flex items-center px-10">
                    <div className="text-white">
                        <h1 className="text-3xl font-bold leading-tight">
                            Predict the Price of<br />Houses in Nepal 🏠
                        </h1>
                        <p className="text-blue-200 mt-2 text-sm">
                            Get an estimated price based on location, size, features and other important factors.
                        </p>
                    </div>
                </div>
            </div>

            {/* MAIN CONTENT */}
            <div className="max-w-6xl mx-auto px-6 py-8 grid grid-cols-3 gap-6">

                {/* LEFT — FORM */}
                <div className="col-span-1 bg-white rounded-2xl shadow p-6">
                    <h2 className="text-blue-700 font-semibold text-lg mb-4 flex items-center gap-2">
                        👤 Enter House Details
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">

                        {/* Location */}
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
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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

                        {/* Land Area */}
                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">📐 Land Area (sq ft)</label>
                            <input
                                type="number"
                                name="land_area"
                                value={form.land_area}
                                onChange={handleChange}
                                placeholder="e.g. 1500"
                                required
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Road Access */}
                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">🛣️ Road Access (ft)</label>
                            <select
                                name="road_access"
                                value={form.road_access}
                                onChange={handleChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {ROAD_ACCESS_OPTIONS.map((v) => (
                                    <option key={v} value={v}>{v} ft</option>
                                ))}
                            </select>
                        </div>

                        {/* Facing */}
                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">🧭 Facing</label>
                            <select
                                name="facing_encoded"
                                value={form.facing_encoded}
                                onChange={handleChange}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {FACING_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Floor / Bedroom / Bathroom */}
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
                                        className="w-full border border-gray-200 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            ))}
                        </div>

                        {/* Property Age */}
                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase mb-1 block">📅 Property Age (Years)</label>
                            <input
                                type="number"
                                name="property_age"
                                value={form.property_age}
                                onChange={handleChange}
                                placeholder="e.g. 10"
                                required
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Amenities */}
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

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={loading || !form.location_encoded}
                            className="w-full bg-blue-700 text-white py-3 rounded-lg font-semibold hover:bg-blue-800 transition disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? "Predicting..." : "📈 Predict Price"}
                        </button>

                        {error && <p className="text-red-500 text-sm text-center">{error}</p>}
                    </form>
                </div>

                {/* RIGHT — RESULT */}
                <div className="col-span-2 space-y-6">
                    {!result ? (
                        <div className="bg-white rounded-2xl shadow p-10 flex flex-col items-center justify-center text-center h-full min-h-64">
                            <div className="text-6xl mb-4">🏠</div>
                            <p className="text-gray-400 text-lg">Fill in the details and click</p>
                            <p className="text-blue-700 font-semibold text-lg">Predict Price</p>
                        </div>
                    ) : (
                        <>
                            {/* Price Result */}
                            <div className="bg-white rounded-2xl shadow p-6 flex justify-between items-center">
                                <div>
                                    <p className="text-gray-500 text-sm mb-1">Estimated Price</p>
                                    <p className="text-4xl font-bold text-blue-700">
                                        Rs. {result.predicted_price.toLocaleString("en-IN")}
                                    </p>
                                    <p className="text-gray-500 mt-1">({result.predicted_price_cr})</p>
                                    {selectedLocation && (
                                        <p className="text-green-600 text-sm mt-2">
                                            📍 {selectedLocation.label}
                                        </p>
                                    )}
                                </div>
                                <div className="text-8xl">🏡</div>
                            </div>

                            {/* Key Factors — Real SHAP Values */}
                            <div className="bg-white rounded-2xl shadow p-6">
                                <h3 className="font-semibold text-gray-700 mb-4">
                                    Key Factors Influencing Price
                                    <span className="text-xs text-gray-400 font-normal ml-2">(powered by SHAP)</span>
                                </h3>
                                {result.shap_values.slice(0, 6).map((item) => {
                                    const isPositive = item.shap_value > 0;
                                    const maxVal = Math.max(
                                        ...result.shap_values.slice(0, 6).map((i) => Math.abs(i.shap_value))
                                    );
                                    const pct = Math.round((Math.abs(item.shap_value) / maxVal) * 100);
                                    const friendlyNames = {
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
                                    return (
                                        <div key={item.feature} className="flex items-center gap-3 mb-3">
                                            <span className="text-sm text-gray-600 w-36">
                                                {friendlyNames[item.feature] || item.feature}
                                            </span>
                                            <div className="flex-1 bg-gray-100 rounded-full h-2">
                                                <div
                                                    className={`h-2 rounded-full ${isPositive ? "bg-green-500" : "bg-blue-500"}`}
                                                    style={{ width: `${pct}%` }}
                                                />
                                            </div>
                                            <span className={`text-xs w-24 text-right font-medium ${isPositive ? "text-green-600" : "text-blue-600"}`}>
                                                {isPositive ? "▲" : "▼"} Rs.{Math.abs(item.shap_value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                                            </span>
                                        </div>
                                    );
                                })}
                                <p className="text-xs text-gray-400 mt-3">
                                    🟢 Green = pushing price up &nbsp;|&nbsp; 🔵 Blue = pushing price down
                                </p>
                            </div>

                            {/* About Prediction */}
                            <div className="bg-white rounded-2xl shadow p-6">
                                <div className="flex items-start gap-3">
                                    <span className="text-blue-500 text-xl">ℹ️</span>
                                    <div>
                                        <p className="font-semibold text-gray-700 mb-1">About This Prediction</p>
                                        <p className="text-sm text-gray-500">
                                            This price is predicted using a machine learning model trained on
                                            historical house sale data from different locations in Nepal.
                                        </p>
                                        <div className="mt-3 flex items-center gap-2 text-green-600 text-sm font-medium">
                                            ✅ Model Accuracy (R² Score): 0.6719
                                        </div>
                                        <div className="mt-1 text-sm text-gray-400">
                                            📅 Predicted on: {new Date().toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" })}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}