const CITY_COORDINATES = {
  Kathmandu: { lat: 27.7172, lon: 85.324, zoom: 12 },
  Lalitpur: { lat: 27.6588, lon: 85.3247, zoom: 12 },
  Bhaktapur: { lat: 27.671, lon: 85.4298, zoom: 12 },
  Kaski: { lat: 28.2096, lon: 83.9856, zoom: 12 },
  Chitwan: { lat: 27.6761, lon: 84.43, zoom: 11 },
  Sunsari: { lat: 26.6646, lon: 87.2718, zoom: 11 },
  Kavrepalanchok: { lat: 27.6325, lon: 85.5214, zoom: 11 },
};

const AREA_COORDINATES = {
  Imadol: { lat: 27.659, lon: 85.352 },
  Satdobato: { lat: 27.651, lon: 85.326 },
  Bhaisepati: { lat: 27.642, lon: 85.299 },
  Chabahil: { lat: 27.716, lon: 85.347 },
  Budhanilkantha: { lat: 27.783, lon: 85.363 },
  Baluwatar: { lat: 27.728, lon: 85.33 },
  Baneshwor: { lat: 27.691, lon: 85.342 },
  Bansbari: { lat: 27.745, lon: 85.338 },
  Bouddha: { lat: 27.721, lon: 85.361 },
  Dhapasi: { lat: 27.752, lon: 85.329 },
  Dhumbarahi: { lat: 27.737, lon: 85.337 },
  Gongabu: { lat: 27.738, lon: 85.313 },
  Gyaneshwor: { lat: 27.711, lon: 85.333 },
  Jawalakhel: { lat: 27.672, lon: 85.313 },
  Jhamsikhel: { lat: 27.678, lon: 85.311 },
  Kalanki: { lat: 27.693, lon: 85.281 },
  Kapan: { lat: 27.742, lon: 85.369 },
  Koteshwor: { lat: 27.679, lon: 85.349 },
  Kupandole: { lat: 27.685, lon: 85.318 },
  Lazimpat: { lat: 27.722, lon: 85.32 },
  Maharajgunj: { lat: 27.739, lon: 85.337 },
  Naxal: { lat: 27.714, lon: 85.326 },
  Sanepa: { lat: 27.684, lon: 85.307 },
  Sitapaila: { lat: 27.715, lon: 85.274 },
  Swoyambhu: { lat: 27.714, lon: 85.29 },
  Thamel: { lat: 27.715, lon: 85.312 },
  Tikathali: { lat: 27.666, lon: 85.374 },
  Tokha: { lat: 27.771, lon: 85.329 },
  Pokhara: { lat: 28.2096, lon: 83.9856 },
  Itahari: { lat: 26.6646, lon: 87.2718 },
};

function splitLocation(label) {
  const [area, city] = String(label || "")
    .split(",")
    .map((part) => part.trim());
  return { area, city };
}

function getCoordinates(label) {
  const { area, city } = splitLocation(label);
  return AREA_COORDINATES[area] || CITY_COORDINATES[city] || CITY_COORDINATES.Kathmandu;
}

export default function LocationMap({ locationLabel, compact = false }) {
  const coordinates = getCoordinates(locationLabel);
  const label = locationLabel || "Kathmandu, Nepal";
  const delta = coordinates.zoom >= 12 ? 0.035 : 0.08;
  const bbox = [
    coordinates.lon - delta,
    coordinates.lat - delta,
    coordinates.lon + delta,
    coordinates.lat + delta,
  ].join("%2C");
  const src = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${coordinates.lat}%2C${coordinates.lon}`;
  const osmLink = `https://www.openstreetmap.org/?mlat=${coordinates.lat}&mlon=${coordinates.lon}#map=${coordinates.zoom}/${coordinates.lat}/${coordinates.lon}`;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Location on Map</h3>
          <p className="text-[11px] text-gray-400 mt-1">
            Approximate pin for {label}
          </p>
        </div>
        <a
          href={osmLink}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-medium text-blue-700 hover:text-blue-900"
        >
          Open map
        </a>
      </div>
      <div className="relative">
        <iframe
          title={`Map view for ${label}`}
          src={src}
          className={`w-full border-0 ${compact ? "h-[120px]" : "h-72"}`}
          loading="lazy"
        />
        <div
          aria-hidden="true"
          className={`pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-blue-600 bg-blue-500/20 shadow-[0_0_0_8px_rgba(37,99,235,0.08)] ${compact ? "h-20 w-20" : "h-28 w-28"}`}
        />
      </div>
    </div>
  );
}
