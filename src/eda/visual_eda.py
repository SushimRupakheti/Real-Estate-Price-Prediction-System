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

plt.figure(figsize=(12,8))

sns.heatmap(
    numeric_data.corr(),
    annot=True,
    cmap="coolwarm"
)

plt.title("Correlation Heatmap")

plt.show()