import pandas as pd

data = pd.read_csv(
    r"C:\Users\ASUS\Desktop\prediction_model\data\processed\cleaned_house_data.csv"
)

print(data.head())
print(data.shape)

print("\nNUMERICAL SUMMARY")
print(data.describe())

# =====================================
# IQR OUTLIER DETECTION
# =====================================

def detect_outliers(df, column):

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df[
        (df[column] < lower_bound) |
        (df[column] > upper_bound)
    ]

    print(f"\n{column}")
    print(f"Q1 = {Q1}")
    print(f"Q3 = {Q3}")
    print(f"IQR = {IQR}")
    print(f"Lower Bound = {lower_bound}")
    print(f"Upper Bound = {upper_bound}")
    print(f"Outliers Found = {len(outliers)}")

    return outliers


detect_outliers(data, "PRICE")
detect_outliers(data, "LAND AREA (sqft)")
detect_outliers(data, "BEDROOM")
detect_outliers(data, "BATHROOM")
detect_outliers(data, "FLOOR")

bedroom_outliers = data[data["BEDROOM"] > 9]

print("\nBEDROOM OUTLIERS")
print(
    bedroom_outliers[
        ["PRICE", "BEDROOM", "BATHROOM", "FLOOR", "LAND AREA (sqft)"]
    ]
)

bathroom_outliers = data[data["BATHROOM"] > 8]

print("\nBATHROOM OUTLIERS")
print(
    bathroom_outliers[
        ["PRICE", "BEDROOM", "BATHROOM", "FLOOR"]
    ]
)

print("\nShape Before Filtering:", data.shape)

data = data[
    (data["BEDROOM"] <= 10) &
    (data["BATHROOM"] <= 10)
]

print("Shape After Filtering:", data.shape)

print(data.columns.tolist())
print(data.dtypes)