from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from infrastructure_index.service import InfrastructureIndexService

from .config import DEFAULT_SCENARIO_RULES_PATH, load_scenario_rules
from .rules import ScenarioValidationError, get_scenario_definition, match_index_change
from .simulator import apply_change


def format_npr(amount: float) -> str:
    return f"NPR {amount / 10_000_000:.2f} Crore"


class ScenarioService:
    def __init__(self, rules_path: str | Path = DEFAULT_SCENARIO_RULES_PATH, index_service=None):
        self.rules_path = Path(rules_path)
        self.index_service = index_service or InfrastructureIndexService()

    @staticmethod
    def _category_scores(index: dict) -> dict[str, int]:
        return {key: value["score"] for key, value in index["categories"].items()}

    @staticmethod
    def _clamp_score(score: int, rules: dict) -> int:
        return max(rules["score_caps"]["minimum"], min(rules["score_caps"]["maximum"], score))

    def calculate_value_shift(self, baseline_price: float, index_change: int, rules: dict) -> dict:
        band = match_index_change(index_change, rules)
        minimum_percent = max(band["shift_percent_min"], rules["value_shift_caps"]["minimum_percent"])
        maximum_percent = min(band["shift_percent_max"], rules["value_shift_caps"]["maximum_percent"])
        minimum_value = round(baseline_price * (1 + minimum_percent / 100))
        maximum_value = round(baseline_price * (1 + maximum_percent / 100))
        return {
            "classification": band["classification"],
            "minimum_percent": minimum_percent,
            "maximum_percent": maximum_percent,
            "minimum_value": minimum_value,
            "maximum_value": maximum_value,
            "minimum_value_formatted": format_npr(minimum_value),
            "maximum_value_formatted": format_npr(maximum_value),
            "method": "rule_based_infrastructure_scenario",
            "is_forecast": False,
            "statistically_validated": False,
        }

    def simulate(self, request: dict) -> dict:
        rules = load_scenario_rules(self.rules_path)
        baseline_price = request["baseline_price"]
        current_indicators = deepcopy(request["current_infrastructure"])
        changes = request.get("changes", [])

        quantities_by_type = {}
        non_facility_types = set()
        for change in changes:
            definition = get_scenario_definition(change["type"], rules)
            if definition["kind"] == "facility":
                quantity = change.get("quantity")
                if quantity is None:
                    raise ScenarioValidationError(f"{change['type']} requires quantity.")
                quantities_by_type[change["type"]] = quantities_by_type.get(change["type"], 0) + quantity
                if quantities_by_type[change["type"]] > definition["maximum_quantity"]:
                    raise ScenarioValidationError(
                        f"{change['type']} total quantity exceeds configured maximum of {definition['maximum_quantity']}."
                    )
            elif change["type"] in non_facility_types:
                raise ScenarioValidationError(f"Only one {change['type']} change is allowed per simulation.")
            else:
                non_facility_types.add(change["type"])

        total_quantity = sum(change.get("quantity") or 0 for change in changes)
        if total_quantity > rules["maximum_total_quantity"]:
            raise ScenarioValidationError(
                f"Total facility quantity exceeds configured maximum of {rules['maximum_total_quantity']}."
            )

        current_index = self.index_service.calculate_from_indicators(current_indicators)
        running_indicators = deepcopy(current_indicators)
        running_index = current_index
        contributions = []

        for change in changes:
            definition = get_scenario_definition(change["type"], rules)
            next_indicators, description, categories = apply_change(
                running_indicators, change, definition, rules,
            )
            next_index = self.index_service.calculate_from_indicators(next_indicators)
            for category in categories:
                before = running_index["categories"][category]["score"]
                after = next_index["categories"][category]["score"]
                contributions.append({
                    "change": description,
                    "change_type": change["type"],
                    "category": category,
                    "current_category_score": before,
                    "scenario_category_score": after,
                    "score_difference": after - before,
                })
            running_indicators, running_index = next_indicators, next_index

        current_score = self._clamp_score(current_index["overall_score"], rules)
        scenario_score = self._clamp_score(running_index["overall_score"], rules)
        index_change = scenario_score - current_score
        current_categories = self._category_scores(current_index)
        scenario_categories = self._category_scores(running_index)
        differences = {key: scenario_categories[key] - value for key, value in current_categories.items()}

        return {
            "baseline_price": {"amount": round(baseline_price), "formatted": format_npr(baseline_price)},
            "current": {
                "overall_index": current_score,
                "classification": current_index["classification"],
                "category_scores": current_categories,
                "infrastructure": current_indicators,
            },
            "scenario": {
                "overall_index": scenario_score,
                "classification": running_index["classification"],
                "index_change": index_change,
                "category_scores": scenario_categories,
                "category_score_differences": differences,
                "infrastructure": running_indicators,
            },
            "value_shift": self.calculate_value_shift(baseline_price, index_change, rules),
            "rule_contributions": contributions,
            "metadata": {
                "rules_version": rules["version"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "disclaimer": rules["disclaimer"],
                "temporary_copy": True,
            },
        }
