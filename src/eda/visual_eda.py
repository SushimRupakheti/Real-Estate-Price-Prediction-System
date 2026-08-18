import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv(
    r"C:\Users\ASUS\Desktop\prediction_model\data\processed\cleaned_house_data.csv"
)

plt.figure(figsize=(10,6))

sns.histplot(
    data["PRICE"],
    bins=30,
    kde=True
)

plt.title("Price Distribution")
plt.show()

plt.figure(figsize=(10,6))

sns.scatterplot(
    x=data["LAND AREA (sqft)"],
    y=data["PRICE"]
)

plt.title("Land Area vs Price")

plt.show()

top_locations = (
    data.groupby("LOCATION")["PRICE"]
    .mean()
    .sort_values(ascending=False)
    .head(15)
)

plt.figure(figsize=(12,6))

top_locations.plot(kind="bar")

plt.title("Top 15 Most Expensive Locations")

plt.ylabel("Average Price")

plt.show()

numeric_data = data.select_dtypes(
    include=["float64","int64"]
)

readable_labels = {
    "PRICE": "Price",
    "FLOOR": "Floors",
    "BEDROOM": "Bedrooms",
    "BATHROOM": "Bathrooms",
    "LAND AREA (sqft)": "Land area",
    "ROAD ACCESS (ft)": "Road access",
    "PROPERTY AGE": "Property age",
    "HAS_PARKING": "Parking",
    "HAS_BALCONY": "Balcony",
    "HAS_GARDEN": "Garden",
    "HAS_MODULAR_KITCHEN": "Modular kitchen",
    "LOCATION_ENCODED": "Location (encoded)",
}

correlation = numeric_data.corr().rename(
    index=readable_labels,
    columns=readable_labels,
)

plt.figure(figsize=(14,10))

ax = sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5,
    cbar_kws={"shrink": 0.85},
)

ax.set_title("Correlation Heatmap", pad=16, fontsize=16)
ax.set_xticklabels(
    ax.get_xticklabels(),
    rotation=45,
    ha="right",
    rotation_mode="anchor",
    fontsize=9,
)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)

plt.tight_layout()
plt.savefig(
    "visualizations/chart images/Figure_2(correlation_heatmap).png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()
