import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\raw\Nepali_house_dataset.csv")

data = df.copy()

print("Dataset loaded successfully")
print("Original Shape:", data.shape)

# STEP 0: Keep ONLY HOUSE FOR SALE

data = data[data["TITLE"].str.contains("House for Sale", case=False, na=False)]

print("\n Keeping ONLY 'House for Sale':")
print("Shape:", data.shape)

# Optional: reset index (clean structure)
data = data.reset_index(drop=True)

#------------------------------------------------------------------------------------------------------
#Step-1 - converting the cr into numbers
#------------------------------------------------------------------------------------------------------


def clean_price(price):
    if pd.isna(price):
        return np.nan

    price = str(price).lower()
    price = price.replace("rs.", "").replace("rs", "").strip()

    # Case 1: Crore
    if "cr" in price:
        try:
            value = float(price.replace("cr", "").strip())
            return value * 10000000
        except:
            return np.nan

    # Case 2: Lakh (future-proofing)
    if "lakh" in price:
        try:
            value = float(price.replace("lakh", "").strip())
            return value * 100000
        except:
            return np.nan

    # Case 3: plain number
    try:
        return float(price)
    except:
        return np.nan


data["PRICE"] = data["PRICE"].apply(clean_price)

print("\nPRICE CLEANING DONE")
print(data["PRICE"].head(10))
print("\nMissing prices:", data["PRICE"].isna().sum())


#------------------------------------------------------------------------------------------------------
#Step -2 removing the missing price rows
#------------------------------------------------------------------------------------------------------

before = data.shape[0]

data = data.dropna(subset=["PRICE"])

after = data.shape[0]

print("\nRemoved missing PRICE rows")
print("Before:", before)
print("After:", after)
print("Dropped:", before - after)

# =====================================
# STEP 3: CLEAN LAND AREA
# =====================================

def convert_land_area(area):
    if pd.isna(area):
        return np.nan

    area = str(area).lower().strip()

    # Case 1: aana
    if "aana" in area:
        try:
            value = float(area.replace("aana", "").strip())
            return value * 342.25
        except:
            return np.nan

    # Case 2: ropani
    if "ropani" in area:
        try:
            value = float(area.replace("ropani", "").strip())
            return value * 5476
        except:
            return np.nan

    # Case 3: already sq ft
    if "sq" in area:
        try:
            return float(area.replace("sq.ft", "").replace("sq ft", "").strip())
        except:
            return np.nan

    return np.nan


data["LAND AREA (sqft)"] = data["LAND AREA"].apply(convert_land_area)

print("\nLAND AREA CLEANING DONE")
print(data[["LAND AREA", "LAND AREA (sqft)"]].head(10))

print("\nMissing LAND AREA values:", data["LAND AREA (sqft)"].isna().sum())

# =====================================
# STEP : 4- DROP HIGH MISSING COLUMN
# =====================================

print("\nDropping BUILDUP AREA due to high missing values...")

data.drop(columns=["BUILDUP AREA"], inplace=True)

print("BUILDUP AREA dropped")
print("Remaining columns:", data.columns)

# =====================================
# step-5:REMOVE ORIGINAL LAND AREA COLUMN
# =====================================

data.drop(columns=["LAND AREA"], inplace=True)

print("Remaining columns:")
print(data.columns)


# =====================================
# STEP 6: CLEAN ROAD ACCESS
# =====================================

def clean_road_access(value):
    if pd.isna(value):
        return np.nan

    value = str(value).lower().replace("feet", "").strip()

    # Handle ranges like "12-18"
    if "-" in value:
        try:
            parts = value.split("-")
            return (float(parts[0]) + float(parts[1])) / 2
        except:
            return np.nan

    try:
        return float(value)
    except:
        return np.nan


data["ROAD ACCESS (ft)"] = data["ROAD ACCESS"].apply(clean_road_access)

print("\nROAD ACCESS CLEANED")
print(data[["ROAD ACCESS", "ROAD ACCESS (ft)"]].head(10))

print("\nMissing ROAD ACCESS values:", data["ROAD ACCESS (ft)"].isna().sum())

# =====================================
# STEP 7: CLEAN FACING COLUMN
# =====================================

data["FACING"] = data["FACING"].str.lower().str.strip()

print("\nFACING CLEANED")
print(data["FACING"].value_counts().head(10))

print("\nMissing FACING values:", data["FACING"].isna().sum())

# =====================================
# STEP 8: CONVERT BUILT YEAR → PROPERTY AGE
# =====================================

CURRENT_YEAR_BS = 2082  # adjust if needed

def convert_built_year(year):
    if pd.isna(year):
        return np.nan

    try:
        year = str(year).replace("B.S", "").strip()
        year = float(year)
        return CURRENT_YEAR_BS - year
    except:
        return np.nan


data["PROPERTY AGE"] = data["BUILT YEAR"].apply(convert_built_year)

print("\nPROPERTY AGE CREATED")
print(data[["BUILT YEAR", "PROPERTY AGE"]].head(10))

print("\nMissing PROPERTY AGE values:", data["PROPERTY AGE"].isna().sum())

# =====================================
# STEP 9: AMENITIES FEATURE ENGINEERING
# =====================================

import ast

def clean_amenities(text):
    if pd.isna(text):
        return []

    try:
        return ast.literal_eval(text)
    except:
        return []


data["AMENITIES"] = data["AMENITIES"].apply(clean_amenities)

# Create important binary features
data["HAS_PARKING"] = data["AMENITIES"].apply(lambda x: 1 if "Parking" in x else 0)
data["HAS_BALCONY"] = data["AMENITIES"].apply(lambda x: 1 if "Balcony" in x else 0)
data["HAS_GARDEN"] = data["AMENITIES"].apply(lambda x: 1 if "Garden" in x else 0)
data["HAS_MODULAR_KITCHEN"] = data["AMENITIES"].apply(lambda x: 1 if "Modular Kitchen" in x else 0)

print("\nAMENITIES ENGINEERED")
print(data[["HAS_PARKING", "HAS_BALCONY", "HAS_GARDEN", "HAS_MODULAR_KITCHEN"]].head(10))

# =====================================
# STEP 10: FINAL CLEANUP (ML READY DATASET)
# =====================================

# Drop raw/unnecessary columns
# Safe drop (prevents crash if column not found)
data.drop(columns=[
    "TITLE",
    "LAND AREA",
    "BUILT YEAR",
    "AMENITIES"
], inplace=True, errors="ignore")

print("\nDropped raw text columns")

# Handle missing values (simple strategy for now)
data["FLOOR"] = data["FLOOR"].fillna(data["FLOOR"].median())
data["BEDROOM"] = data["BEDROOM"].fillna(data["BEDROOM"].median())
data["BATHROOM"] = data["BATHROOM"].fillna(data["BATHROOM"].median())
data["PROPERTY AGE"] = data["PROPERTY AGE"].fillna(data["PROPERTY AGE"].median())
data["ROAD ACCESS (ft)"] = data["ROAD ACCESS (ft)"].fillna(data["ROAD ACCESS (ft)"].median())
data["FACING"] = data["FACING"].fillna(data["FACING"].mode()[0])

print("\nMissing values handled")

# Final dataset check
print("\nFINAL DATASET INFO:")
print(data.info())

print("\nFinal shape:", data.shape)

# =====================================
# STEP 11: ENCODE FACING (ONE-HOT)
# =====================================

# =====================================
# STEP 11: LOCATION TARGET ENCODING
# =====================================

print("\nEncoding LOCATION using target mean...")

# Calculate mean price per location
location_mean = data.groupby("LOCATION")["PRICE"].mean()

# Map it back to dataset
data["LOCATION_ENCODED"] = data["LOCATION"].map(location_mean)

print("\nLOCATION encoding sample:")
print(data[["LOCATION", "LOCATION_ENCODED"]].head(10))

print("\nMissing LOCATION encoding:", data["LOCATION_ENCODED"].isna().sum())

data.to_csv(
    r"C:\Users\ASUS\Desktop\prediction_model\data\processed\cleaned_house_data.csv",
    index=False
)

print("\nCleaned dataset saved successfully!")