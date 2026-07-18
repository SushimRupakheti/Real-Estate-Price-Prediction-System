import json
from pathlib import Path


DEFAULT_SCENARIO_RULES_PATH = Path(__file__).resolve().parents[3] / "config" / "scenario_rules.json"


class ScenarioConfigurationError(ValueError):
    pass


def load_scenario_rules(path: str | Path = DEFAULT_SCENARIO_RULES_PATH) -> dict:
    try:
        rules = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioConfigurationError(f"Unable to load scenario rules: {exc}") from exc

    required = {
        "version", "disclaimer", "maximum_total_quantity", "scenario_types",
        "road_hierarchy", "index_change_rules", "value_shift_caps", "score_caps",
    }
    missing = required - rules.keys()
    if missing:
        raise ScenarioConfigurationError(f"Scenario configuration is missing: {', '.join(sorted(missing))}")
    if not rules["scenario_types"] or not rules["road_hierarchy"]:
        raise ScenarioConfigurationError("Scenario types and road hierarchy cannot be empty.")
    if rules["maximum_total_quantity"] < 0:
        raise ScenarioConfigurationError("Maximum total quantity cannot be negative.")

    bands = sorted(rules["index_change_rules"], key=lambda item: item["min_change"])
    if not bands or bands[0]["min_change"] > -100 or bands[-1]["max_change"] < 100:
        raise ScenarioConfigurationError("Index-change rules must cover -100 through 100.")
    for previous, current in zip(bands, bands[1:]):
        if previous["max_change"] + 1 != current["min_change"]:
            raise ScenarioConfigurationError("Index-change rules must be continuous and non-overlapping.")
    for band in bands:
        if band["min_change"] > band["max_change"]:
            raise ScenarioConfigurationError("Index-change rule minimum cannot exceed maximum.")
        if band["shift_percent_min"] > band["shift_percent_max"]:
            raise ScenarioConfigurationError("Value-shift minimum cannot exceed maximum.")
    return rules
