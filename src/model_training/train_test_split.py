import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Load cleaned dataset
data = pd.read_csv(
    r"C:\Users\ASUS\Desktop\prediction_model\data\processed\cleaned_house_data.csv"
)

print("Dataset Loaded")
print(data.shape)

# -------------------------
# FILTER (if not already done)
# -------------------------
data = data[
    (data["BEDROOM"] <= 10) &
    (data["BATHROOM"] <= 10)
]
print("After Filter:", data.shape)

# -------------------------
# FILTER EXTREME OUTLIERS
# -------------------------
data = data[data["PRICE"] <= 100000000]  # Remove properties > 10 Cr
print("After Price Cap (<=10 Cr):", data.shape)


# Standardize FACING values
data["FACING"] = data["FACING"].str.strip().str.lower()
data["FACING"] = data["FACING"].str.replace(" ", "-", regex=False)
data["FACING"] = data["FACING"].replace("west-/-north", "north-west")

print("\nFACING After Cleaning:")
print(data["FACING"].value_counts())

# -------------------------
# ENCODE FACING
# -------------------------
print("\nFACING Values:")
print(data["FACING"].value_counts())

le = LabelEncoder()
data["FACING_ENCODED"] = le.fit_transform(data["FACING"].astype(str))
# -------------------------
# FEATURE ENGINEERING
# -------------------------

# Price per sqft proxy features
data["AREA_PER_BEDROOM"] = data["LAND AREA (sqft)"] / data["BEDROOM"]
data["TOTAL_ROOMS"]      = data["BEDROOM"] + data["BATHROOM"]
data["IS_NEW"]           = (data["PROPERTY AGE"] <= 2).astype(int)

print("\nNew Features Added:")
print(data[["AREA_PER_BEDROOM", "TOTAL_ROOMS", "IS_NEW"]].head())
# -------------------------
# FEATURES (X) & TARGET (y)
# -------------------------
X = data.drop(columns=["PRICE", "LOCATION", "FACING"])
y = data["PRICE"]

print("\nFeatures:", X.columns.tolist())
print("X shape:", X.shape)
print("y shape:", y.shape)

# -------------------------
# TRAIN TEST SPLIT
# -------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\nTrain Shape:", X_train.shape)
print("Test Shape :", X_test.shape)

# -------------------------
# SAVE
# -------------------------
X_train.to_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv", index=False)
X_test.to_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_test.csv", index=False)
y_train.to_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_train.csv", index=False)
y_test.to_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_test.csv", index=False)

print("\nTrain-Test Split Saved Successfully")