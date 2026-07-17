import { useEffect, useState } from "react";
import axios from "axios";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const CITY_COORDINATES = {
  Kathmandu: { lat: 27.7172, lon: 85.324, zoom: 12 }, Lalitpur: { lat: 27.6588, lon: 85.3247, zoom: 12 },
  Bhaktapur: { lat: 27.671, lon: 85.4298, zoom: 12 }, Kaski: { lat: 28.2096, lon: 83.9856, zoom: 12 },
  Chitwan: { lat: 27.6761, lon: 84.43, zoom: 11 }, Sunsari: { lat: 26.6646, lon: 87.2718, zoom: 11 },
  Kavrepalanchok: { lat: 27.6325, lon: 85.5214, zoom: 11 },
};
const AREA_COORDINATES = {
  Imadol: { lat: 27.659, lon: 85.352 }, Satdobato: { lat: 27.651, lon: 85.326 },
  Bhaisepati: { lat: 27.642, lon: 85.299 }, Chabahil: { lat: 27.716, lon: 85.347 },
  Budhanilkantha: { lat: 27.783, lon: 85.363 }, Baluwatar: { lat: 27.728, lon: 85.33 },
  Baneshwor: { lat: 27.691, lon: 85.342 }, Bansbari: { lat: 27.745, lon: 85.338 },
  Bouddha: { lat: 27.721, lon: 85.361 }, Dhapasi: { lat: 27.752, lon: 85.329 },
  Dhumbarahi: { lat: 27.737, lon: 85.337 }, Gongabu: { lat: 27.738, lon: 85.313 },
  Gyaneshwor: { lat: 27.711, lon: 85.333 }, Jawalakhel: { lat: 27.672, lon: 85.313 },
  Jhamsikhel: { lat: 27.678, lon: 85.311 }, Kalanki: { lat: 27.693, lon: 85.281 },
  Kapan: { lat: 27.742, lon: 85.369 }, Koteshwor: { lat: 27.679, lon: 85.349 },
  Kupandole: { lat: 27.685, lon: 85.318 }, Lazimpat: { lat: 27.722, lon: 85.32 },
  Maharajgunj: { lat: 27.739, lon: 85.337 }, Naxal: { lat: 27.714, lon: 85.326 },
  Sanepa: { lat: 27.684, lon: 85.307 }, Sitapaila: { lat: 27.715, lon: 85.274 },
  Swoyambhu: { lat: 27.714, lon: 85.29 }, Thamel: { lat: 27.715, lon: 85.312 },
  Tikathali: { lat: 27.666, lon: 85.374 }, Tokha: { lat: 27.771, lon: 85.329 },
  Pokhara: { lat: 28.2096, lon: 83.9856 }, Itahari: { lat: 26.6646, lon: 87.2718 },
};

function getCoordinates(label) {
  const [area, city] = String(label || "").split(",").map((part) => part.trim());
  return AREA_COORDINATES[area] || CITY_COORDINATES[city] || CITY_COORDINATES.Kathmandu;
}

function MapInteraction({ point, onSelect }) {
  const map = useMap();
  useEffect(() => { map.setView([point.lat, point.lon], map.getZoom()); }, [map, point]);
  useMapEvents({ click(event) { onSelect({ lat: event.latlng.lat, lon: event.latlng.lng }); } });
  return <CircleMarker center={[point.lat, point.lon]} radius={9} pathOptions={{ color: "#1d4ed8", fillOpacity: 0.75 }} />;
}

const CATEGORY_COLORS = { schools: "#2563eb", colleges: "#4f46e5", kindergartens: "#7c3aed", hospitals: "#dc2626", clinics: "#f97316", bus_stops: "#0891b2", marketplaces: "#a16207", supermarkets: "#ca8a04", banks: "#059669", parks: "#16a34a" };

function FacilityFocus({ facility }) {
  const map = useMap();
  useEffect(() => { if (facility) map.setView([facility.latitude, facility.longitude], Math.max(map.getZoom(), 16)); }, [facility, map]);
  return null;
}

function FacilityMarkers({ facilities, selectedFacility, onFacilitySelect }) {
  return facilities.map((facility) => {
    const selected = selectedFacility?.osm_id === facility.osm_id && selectedFacility?.osm_type === facility.osm_type;
    return <CircleMarker key={`${facility.osm_type}-${facility.osm_id}-${facility.category}`} center={[facility.latitude, facility.longitude]} radius={selected ? 10 : 6} pathOptions={{ color: CATEGORY_COLORS[facility.category] || "#475569", fillOpacity: selected ? 0.95 : 0.65, weight: selected ? 4 : 2 }} eventHandlers={{ click: () => onFacilitySelect?.(facility) }}>
      <Popup><strong>{facility.name}</strong><br />{facility.category_label}<br />{Math.round(facility.distance_m)} m</Popup>
    </CircleMarker>;
  });
}

export default function LocationMap({ locationLabel, compact = false, onCoordinateChange, onCoordinateConfirm, facilities = [], selectedFacility = null, onFacilitySelect }) {
  const initial = getCoordinates(locationLabel);
  const [point, setPoint] = useState({ lat: initial.lat, lon: initial.lon });
  const [confirmed, setConfirmed] = useState(false);
  const [geocoding, setGeocoding] = useState(false);
  useEffect(() => {
    const next = getCoordinates(locationLabel);
    const fallbackPoint = { lat: next.lat, lon: next.lon };
    setPoint(fallbackPoint); setConfirmed(false); onCoordinateChange?.(fallbackPoint);
    if (!locationLabel?.trim()) return;
    let active = true;
    setGeocoding(true);
    axios.post("http://127.0.0.1:8000/infrastructure/geocode", { location_name: locationLabel })
      .then((response) => {
        if (active) {
          const resolvedPoint = { lat: response.data.latitude, lon: response.data.longitude };
          setPoint(resolvedPoint); onCoordinateChange?.(resolvedPoint);
        }
      })
      .catch(() => {})
      .finally(() => { if (active) setGeocoding(false); });
    return () => { active = false; };
  }, [locationLabel, onCoordinateChange]);

  const confirm = () => { setConfirmed(true); onCoordinateConfirm?.(point); };
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700">Select exact property point</h3>
        <p className="text-[11px] text-gray-500 mt-1">{geocoding ? "Locating the entered area..." : "Click the map to move the marker, then confirm the coordinates."}</p>
      </div>
      <MapContainer center={[point.lat, point.lon]} zoom={initial.zoom || 14} className={`w-full ${compact ? "h-[220px]" : "h-72"}`}>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapInteraction point={point} onSelect={(next) => { setPoint(next); setConfirmed(false); onCoordinateChange?.(next); }} />
        <FacilityMarkers facilities={facilities} selectedFacility={selectedFacility} onFacilitySelect={onFacilitySelect} />
        <FacilityFocus facility={selectedFacility} />
      </MapContainer>
      <div className="p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <p className="text-xs text-gray-600" data-testid="selected-coordinates">
          Lat {point.lat.toFixed(6)}, Lon {point.lon.toFixed(6)}
        </p>
        <button type="button" onClick={confirm} className="bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-semibold">
          {confirmed ? "Point confirmed" : "Confirm property point"}
        </button>
      </div>
    </div>
  );
}
