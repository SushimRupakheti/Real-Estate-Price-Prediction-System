"""Convert OSM elements into narrow, deduplicated current-context indicators."""
import math
import re
import unicodedata

from .config import (
    MAJOR_ROAD_TYPES, PLACE_NAME_DEDUP_DISTANCE_M, RADII_METERS,
    UNNAMED_CROSS_TYPE_DEDUP_DISTANCE_M,
)

EARTH_RADIUS_M = 6_371_000
CATEGORY_RULES = {
    "schools": ({("amenity", "school")}, "school"),
    "colleges": ({("amenity", "college")}, "school"),
    "kindergartens": ({("amenity", "kindergarten")}, "school"),
    "hospitals": ({("amenity", "hospital"), ("healthcare", "hospital")}, "healthcare"),
    "clinics": ({("amenity", "clinic"), ("healthcare", "clinic")}, "healthcare"),
    "bus_stops": ({("highway", "bus_stop"), ("public_transport", "platform")}, "bus_stop"),
    "marketplaces": ({("amenity", "marketplace")}, "market"),
    "supermarkets": ({("shop", "supermarket")}, "market"),
    "banks": ({("amenity", "bank")}, "bank"),
    "parks": ({("leisure", "park")}, "park"),
}


def haversine_m(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    value = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(value))


def _point_segment_distance_m(lat, lon, a_lat, a_lon, b_lat, b_lon):
    scale_x, scale_y = math.cos(math.radians(lat)) * 111_320, 110_540
    ax, ay, bx, by = (a_lon-lon)*scale_x, (a_lat-lat)*scale_y, (b_lon-lon)*scale_x, (b_lat-lat)*scale_y
    dx, dy = bx-ax, by-ay
    if dx == 0 and dy == 0: return math.hypot(ax, ay)
    t = max(0.0, min(1.0, -(ax*dx + ay*dy) / (dx*dx + dy*dy)))
    return math.hypot(ax+t*dx, ay+t*dy)


def _center(element):
    if "lat" in element and "lon" in element: return float(element["lat"]), float(element["lon"])
    center = element.get("center") or {}
    if "lat" in center and "lon" in center: return float(center["lat"]), float(center["lon"])
    geometry = element.get("geometry") or []
    if geometry:
        return (sum(float(p["lat"]) for p in geometry)/len(geometry),
                sum(float(p["lon"]) for p in geometry)/len(geometry))
    return None


def _road_distance(element, latitude, longitude):
    geometry = element.get("geometry") or []
    if len(geometry) >= 2:
        return min(_point_segment_distance_m(latitude, longitude, float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"])) for a,b in zip(geometry, geometry[1:]))
    center = _center(element)
    return None if center is None else haversine_m(latitude, longitude, *center)


def _normalize_name(name):
    if not name: return None
    value = unicodedata.normalize("NFKC", str(name)).casefold().strip()
    return re.sub(r"[^\w]+", " ", value).strip() or None


def _references(tags):
    keys = ("wikidata", "brand:wikidata", "ref", "ref:operator", "operator:wikidata")
    return {(key, str(tags[key]).casefold().strip()) for key in keys if tags.get(key)}


def _point_in_polygon(latitude, longitude, geometry):
    if len(geometry) < 4: return False
    points = [(float(point["lon"]), float(point["lat"])) for point in geometry]
    inside = False; x, y = longitude, latitude
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        if (y1 > y) != (y2 > y):
            crossing_x = (x2-x1) * (y-y1) / (y2-y1) + x1
            if x < crossing_x: inside = not inside
    return inside


def _matches_category(tags, category, rules):
    matched = [(key, value) for key, value in rules if tags.get(key) == value]
    if category == "bus_stops" and ("public_transport", "platform") in matched and tags.get("bus") != "yes":
        matched.remove(("public_transport", "platform"))
    return matched


def _candidates(elements, category, rules, radius_key, latitude, longitude):
    candidates, seen = [], set()
    for element in elements:
        identity = (element.get("type"), element.get("id"))
        if identity in seen: continue
        seen.add(identity)
        tags = element.get("tags") or {}
        matched = _matches_category(tags, category, rules)
        center = _center(element)
        if not matched or center is None: continue
        distance = haversine_m(latitude, longitude, *center)
        if distance > RADII_METERS[radius_key]: continue
        candidates.append({
            "element_type": element.get("type"), "osm_id": element.get("id"),
            "name": tags.get("name"), "normalized_name": _normalize_name(tags.get("name")),
            "latitude": center[0], "longitude": center[1], "distance_m": distance,
            "matched_tags": {key: value for key, value in matched},
            "reason": f"Matched {', '.join(f'{k}={v}' for k,v in matched)} within {RADII_METERS[radius_key]} m",
            "references": _references(tags), "category": category,
            "geometry": element.get("geometry") or [],
        })
    return candidates


def _same_place(candidate, representative):
    distance = haversine_m(candidate["latitude"], candidate["longitude"], representative["latitude"], representative["longitude"])
    if candidate["references"] and representative["references"] and candidate["references"] & representative["references"]:
        return True
    if (_point_in_polygon(candidate["latitude"], candidate["longitude"], representative["geometry"])
            or _point_in_polygon(representative["latitude"], representative["longitude"], candidate["geometry"])):
        return True
    if candidate["normalized_name"] and candidate["normalized_name"] == representative["normalized_name"]:
        return distance <= PLACE_NAME_DEDUP_DISTANCE_M
    # Only merge unnamed objects at near-identical coordinates and across OSM
    # representation types; nearby unnamed facilities remain independent.
    return (not candidate["normalized_name"] and not representative["normalized_name"]
            and candidate["element_type"] != representative["element_type"]
            and candidate["matched_tags"] == representative["matched_tags"]
            and distance <= UNNAMED_CROSS_TYPE_DEDUP_DISTANCE_M)


def _deduplicate(candidates):
    groups = []
    for candidate in sorted(candidates, key=lambda item: item["distance_m"]):
        group = next((group for group in groups if _same_place(candidate, group[0])), None)
        if group is None: groups.append([candidate])
        else: group.append(candidate)
    return groups


def _public_place(candidate):
    return {
        "name": candidate["name"] or "Unnamed facility",
        "osm_id": candidate["osm_id"],
        "osm_type": candidate["element_type"],
        "latitude": round(candidate["latitude"], 7),
        "longitude": round(candidate["longitude"], 7),
        "distance_m": round(candidate["distance_m"], 1),
        "tags": candidate["matched_tags"],
    }


def calculate_indicators(elements, latitude, longitude, include_debug=False):
    roads, major_roads, seen_roads = [], [], set()
    for element in elements:
        tags = element.get("tags") or {}; highway = tags.get("highway")
        if element.get("type") != "way" or not highway: continue
        identity = (element.get("type"), element.get("id"))
        if identity in seen_roads: continue
        seen_roads.add(identity)
        distance = _road_distance(element, latitude, longitude)
        if distance is None: continue
        center = _center(element)
        road = {"name": tags.get("name") or "Unnamed Road", "distance_m": round(distance, 1),
                "road_type": highway, "highway_classification": highway,
                "osm_id": element.get("id"), "osm_type": element.get("type"),
                "latitude": None if center is None else round(center[0], 7),
                "longitude": None if center is None else round(center[1], 7),
                "tags": {"highway": highway, **({"name": tags["name"]} if tags.get("name") else {})}}
        roads.append(road)
        if highway in MAJOR_ROAD_TYPES: major_roads.append(road)
    nearest = min(roads, key=lambda item: item["distance_m"], default=None)
    nearest_major = min(major_roads, key=lambda item: item["distance_m"], default=None)

    categories, debug = {}, {}
    for category, (rules, radius_key) in CATEGORY_RULES.items():
        candidates = _candidates(elements, category, rules, radius_key, latitude, longitude)
        groups = _deduplicate(candidates)
        places = [_public_place(group[0]) for group in groups]
        places.sort(key=lambda item: item["distance_m"])
        categories[category] = {"raw_count": len(candidates), "deduplicated_count": len(places),
                                "radius_m": RADII_METERS[radius_key], "places": places}
        if include_debug:
            debug[category] = [{k: (sorted(v) if k == "references" else round(v,1) if k == "distance_m" else v)
                                for k,v in group[0].items() if k not in {"normalized_name", "category", "geometry"}}
                               for group in groups[:5]]

    combined_schools = sum(categories[name]["deduplicated_count"] for name in ("schools", "colleges", "kindergartens"))
    combined_health = categories["hospitals"]["deduplicated_count"] + categories["clinics"]["deduplicated_count"]
    combined_markets = categories["marketplaces"]["deduplicated_count"] + categories["supermarkets"]["deduplicated_count"]
    result = {
        "roads": {"nearest_road_distance_m": None if nearest is None else nearest["distance_m"],
                  "nearest_major_road_distance_m": None if nearest_major is None else nearest_major["distance_m"],
                  "nearest_major_road_type": None if nearest_major is None else nearest_major["highway_classification"],
                  "nearest_road": nearest, "nearest_major_road": nearest_major},
        "categories": categories,
        "amenities": {"schools_within_1km": combined_schools, "hospitals_and_clinics_within_2km": combined_health,
                      "bus_stops_within_1km": categories["bus_stops"]["deduplicated_count"],
                      "markets_within_1km": combined_markets, "banks_within_1km": categories["banks"]["deduplicated_count"],
                      "parks_within_2km": categories["parks"]["deduplicated_count"]},
        "connectivity": {"road_network_nodes_within_1km": None, "road_intersections_within_1km": None,
                         "three_way_intersections_within_1km": None, "four_or_more_way_intersections_within_1km": None},
    }
    if include_debug: result["debug"] = debug
    return result
