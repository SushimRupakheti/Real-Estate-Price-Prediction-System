def classify(score: int, classifications: list[dict]) -> str:
    for rule in sorted(classifications, key=lambda item: item["min_score"], reverse=True):
        if score >= rule["min_score"]:
            return rule["label"]
    raise ValueError("Classification rules must cover a minimum score of zero.")


def match_component(value, component: dict, missing_score: int) -> dict:
    if value is None:
        return {
            "score": missing_score,
            "rule": f"{component['label']} is unavailable; configured missing-indicator score applied",
        }

    rule_type = component["type"]
    if rule_type == "categorical":
        match = component["scores"].get(str(value).lower())
        return match or {
            "score": missing_score,
            "rule": f"No configured rule for {component['label']} value '{value}'",
        }

    bands = component["bands"]
    if rule_type == "lower_is_better":
        for band in bands:
            if band["max"] is None or value <= band["max"]:
                return band
    elif rule_type == "higher_is_better":
        for band in bands:
            if value >= band["min"]:
                return band
    raise ValueError(f"Unsupported or unmatched rule type: {rule_type}")
