from copy import deepcopy

from .rules import ScenarioValidationError, validate_road_upgrade


def apply_change(indicators: dict, change: dict, definition: dict, rules: dict) -> tuple[dict, str, list[str]]:
    scenario = deepcopy(indicators)
    kind = definition["kind"]
    indicator = definition["indicator"]

    if kind == "facility":
        quantity = change.get("quantity")
        if quantity is None:
            raise ScenarioValidationError(f"{change['type']} requires quantity.")
        if quantity < 0:
            raise ScenarioValidationError("Facility quantity cannot be negative.")
        if quantity > definition["maximum_quantity"]:
            raise ScenarioValidationError(
                f"{change['type']} quantity exceeds configured maximum of {definition['maximum_quantity']}."
            )
        scenario[indicator] = int(scenario.get(indicator, 0)) + quantity
        suffix = "s" if quantity != 1 else ""
        return scenario, f"Added {quantity} {definition['label']}{suffix}", [definition["category"]]

    if kind == "distance":
        new_distance = change.get("new_distance_m")
        current_distance = scenario.get(indicator)
        if new_distance is None:
            raise ScenarioValidationError(f"{change['type']} requires new_distance_m.")
        if current_distance is None:
            raise ScenarioValidationError(f"Current {definition['label'].lower()} is unavailable.")
        if new_distance < definition["minimum_distance_m"]:
            raise ScenarioValidationError(f"{definition['label']} cannot be negative.")
        if new_distance >= current_distance:
            raise ScenarioValidationError(f"{definition['label']} improvement must be closer than the current distance.")
        if current_distance - new_distance > definition["maximum_reduction_m"]:
            raise ScenarioValidationError(
                f"{definition['label']} reduction exceeds configured maximum of {definition['maximum_reduction_m']} m."
            )
        scenario[indicator] = new_distance
        return scenario, (
            f"{definition['label']} reduced from {round(current_distance):,} m to {round(new_distance):,} m"
        ), definition["categories"]

    if kind == "road_upgrade":
        current_type = scenario.get(indicator)
        new_type = validate_road_upgrade(current_type, change.get("new_road_type"), rules["road_hierarchy"])
        scenario[indicator] = new_type
        return scenario, (
            f"{definition['label']} upgraded from {current_type} to {new_type}"
        ), definition["categories"]

    raise ScenarioValidationError(f"Unsupported scenario rule kind: {kind}")
