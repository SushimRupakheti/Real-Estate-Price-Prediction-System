from .config import ScenarioConfigurationError


class ScenarioValidationError(ValueError):
    pass


def get_scenario_definition(change_type: str, rules: dict) -> dict:
    definition = rules["scenario_types"].get(change_type)
    if definition is None:
        raise ScenarioValidationError(f"Unsupported scenario type: {change_type}")
    return definition


def validate_road_upgrade(current_type: str | None, new_type: str, hierarchy: list[str]):
    normalized_current = str(current_type or "").lower()
    normalized_new = str(new_type or "").lower()
    if normalized_current not in hierarchy:
        raise ScenarioValidationError(f"Current road classification '{current_type}' is not configurable for upgrades.")
    if normalized_new not in hierarchy:
        raise ScenarioValidationError(f"Unsupported road classification: {new_type}")
    if hierarchy.index(normalized_new) <= hierarchy.index(normalized_current):
        raise ScenarioValidationError(
            f"Road upgrade must move upward from {normalized_current}; '{normalized_new}' is not an upgrade."
        )
    return normalized_new


def match_index_change(index_change: int, rules: dict) -> dict:
    for band in rules["index_change_rules"]:
        if band["min_change"] <= index_change <= band["max_change"]:
            return band
    raise ScenarioConfigurationError(f"No value-shift rule covers index change {index_change}.")
