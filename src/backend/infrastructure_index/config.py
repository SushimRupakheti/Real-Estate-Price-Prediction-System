import json
from pathlib import Path


DEFAULT_RULES_PATH = Path(__file__).resolve().parents[3] / "config" / "infrastructure_index_rules.json"


class RuleConfigurationError(ValueError):
    """Raised when the external scoring rules are incomplete or inconsistent."""


def load_rules(path: str | Path = DEFAULT_RULES_PATH) -> dict:
    """Load and validate rules on every call so JSON edits take effect immediately."""
    rules_path = Path(path)
    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleConfigurationError(f"Unable to load Infrastructure Health Index rules: {exc}") from exc

    required = {"version", "classifications", "category_weights", "categories"}
    missing = required - rules.keys()
    if missing:
        raise RuleConfigurationError(f"Rule configuration is missing: {', '.join(sorted(missing))}")

    categories = rules["categories"]
    weights = rules["category_weights"]
    if set(categories) != set(weights):
        raise RuleConfigurationError("Category definitions and category weights must use identical keys.")
    if abs(sum(float(value) for value in weights.values()) - 1.0) > 1e-9:
        raise RuleConfigurationError("Category weights must sum to 1.0.")

    for key, category in categories.items():
        components = category.get("components", [])
        if not components:
            raise RuleConfigurationError(f"Category '{key}' must define at least one component.")
        if abs(sum(float(item["weight"]) for item in components) - 1.0) > 1e-9:
            raise RuleConfigurationError(f"Component weights for '{key}' must sum to 1.0.")
    return rules
