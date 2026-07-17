from datetime import datetime, timezone
from pathlib import Path

from .config import DEFAULT_RULES_PATH, load_rules
from .scoring import calculate_index


COUNT_INDICATORS = (
    "schools", "colleges", "kindergartens", "hospitals", "clinics",
    "marketplaces", "supermarkets", "banks", "bus_stops", "parks",
)


class InfrastructureIndexService:
    def __init__(self, rules_path: str | Path = DEFAULT_RULES_PATH):
        self.rules_path = Path(rules_path)

    @staticmethod
    def extract_indicators(analysis: dict) -> dict:
        roads = analysis["roads"]
        categories = analysis["categories"]
        return {
            "nearest_road_distance_m": roads.get("nearest_road_distance_m"),
            "nearest_major_road_distance_m": roads.get("nearest_major_road_distance_m"),
            "nearest_major_road_type": roads.get("nearest_major_road_type"),
            **{
                name: categories[name]["deduplicated_count"]
                for name in COUNT_INDICATORS
            },
        }

    def calculate(self, analysis: dict) -> dict:
        rules = load_rules(self.rules_path)
        indicators = self.extract_indicators(analysis)
        result = calculate_index(indicators, rules)
        return {
            **result,
            "indicators_used": indicators,
            "selected_location": analysis["selected_location"],
            "metadata": {
                "name": rules.get("index_name", "Infrastructure Health Index"),
                "method": "deterministic_json_rules",
                "rules_version": rules["version"],
                "rules_path": str(self.rules_path),
                "calculated_at": datetime.now(timezone.utc).isoformat(),
                "source": analysis.get("metadata", {}).get("source", "OpenStreetMap contributors"),
                "limitations": [
                    "The index reflects mapped current infrastructure, not verified operating status.",
                    "OpenStreetMap coverage and tagging completeness vary by location.",
                    "The index is a rule-based assessment, not a price model or future-price forecast.",
                ],
            },
        }
