import pandas as pd

df = pd.read_csv(
    r"C:\Users\ASUS\Desktop\prediction_model\data\processed\cleaned_house_data.csv"
)

print(df.head())
print(df.info())


numeric_df = df.select_dtypes(include=["number"])

corr = numeric_df.corr()

print(corr["PRICE"].sort_values(ascending=False))


# ==========================
# MISSING VALUES CHECK
# ==========================

print("\nMISSING VALUES CHECK")
print(df.isnull().sum())