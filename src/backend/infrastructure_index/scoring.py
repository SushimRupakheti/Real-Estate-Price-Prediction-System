from .rules import classify, match_component


def _display_value(value, unit: str | None) -> str:
    if value is None:
        return "Unavailable"
    if unit == "m":
        return f"{round(float(value)):,} m"
    if unit == "places":
        return f"{int(value)} mapped place{'s' if int(value) != 1 else ''}"
    return str(value).title() if isinstance(value, str) else str(value)


def score_category(key: str, category: dict, indicators: dict, rules: dict) -> dict:
    matched_rules = []
    total = 0.0
    for component in category["components"]:
        value = indicators.get(component["indicator"])
        match = match_component(value, component, rules["missing_indicator_score"])
        contribution = float(match["score"]) * float(component["weight"])
        total += contribution
        matched_rules.append({
            "indicator": component["indicator"],
            "label": component["label"],
            "observed_value": value,
            "display_value": _display_value(value, component.get("unit")),
            "matched_rule": match["rule"],
            "component_score": int(match["score"]),
            "component_weight": float(component["weight"]),
            "weighted_contribution": round(contribution, 2),
        })

    score = round(total)
    reason = " ".join(
        f"{item['label']}: {item['display_value']}; matched '{item['matched_rule']}'."
        for item in matched_rules
    )
    return {
        "key": key,
        "label": category["label"],
        "description": category["description"],
        "score": score,
        "classification": classify(score, rules["classifications"]),
        "reason": reason,
        "rules_used": matched_rules,
    }


def calculate_index(indicators: dict, rules: dict) -> dict:
    categories = {
        key: score_category(key, category, indicators, rules)
        for key, category in rules["categories"].items()
    }
    contributions = {
        key: round(category["score"] * float(rules["category_weights"][key]), 2)
        for key, category in categories.items()
    }
    overall_score = round(sum(contributions.values()))
    return {
        "overall_score": overall_score,
        "classification": classify(overall_score, rules["classifications"]),
        "categories": categories,
        "category_weights": rules["category_weights"],
        "weighted_contributions": contributions,
    }
