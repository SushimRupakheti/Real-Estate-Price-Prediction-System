"""Save the shared raw split without fitting preprocessing."""
from compare_model import load_clean_data, split_data, PROCESSED_DIR
if __name__ == "__main__":
    parts = split_data(load_clean_data())
    for name, value in zip(("X_train", "X_test", "y_train", "y_test"), parts):
        value.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
    print(f"Saved raw split: train={len(parts[0])}, test={len(parts[1])}")
