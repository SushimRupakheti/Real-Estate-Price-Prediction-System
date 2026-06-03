# PHASE 2: DATASET UNDERSTANDING


# --- IMPORTS ---
import pandas as pd    # For loading and working with our data table
import numpy as np     # For numerical operations

# --- STEP 1: LOAD THE DATASET ---
# pd.read_csv() reads a CSV file and turns it into a "DataFrame"
# A DataFrame is just a table — like Excel inside Python

df = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\raw\Nepali_house_dataset.csv")
# The 'r' before the string means "raw string" — it stops '\' from causing errors on Windows

print("=" * 60)
print("✅ Dataset loaded successfully!")
print("=" * 60)


# --- STEP 2: HOW BIG IS OUR DATASET? ---
# .shape gives us (number of rows, number of columns)
rows, columns = df.shape

print(f"\n📊 DATASET SIZE:")
print(f"   Rows (houses)  : {rows}")
print(f"   Columns        : {columns}")
# Example output: Rows: 5000, Columns: 13
# Each row = one house listing
# Each column = one piece of information about that house


# --- STEP 3: WHAT ARE OUR COLUMNS? ---
# .columns shows us all column names
print(f"\n📋 COLUMN NAMES:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i:2}. {col}")


# --- STEP 4: PEEK AT THE FIRST 5 ROWS ---
# .head(5) shows us the first 5 rows — like opening the first page of a book
print(f"\n👀 FIRST 5 ROWS OF DATA:")
print(df.head(5).to_string())
# .to_string() shows the full content without cutting it off


# --- STEP 5: DATA TYPES OF EACH COLUMN ---
# This tells us if Python thinks a column is a number or text
# 'object' = text (string), 'int64' = whole number, 'float64' = decimal number
print(f"\n🔤 DATA TYPES OF EACH COLUMN:")
print(df.dtypes)
# We WANT: BEDROOM, BATHROOM, FLOOR to be int/float
# We EXPECT: PRICE, LAND AREA to show as 'object' because of text like "Rs." and "aana"


# --- STEP 6: BASIC STATISTICS ---
# .describe() gives us min, max, average for number columns
# This helps us spot if any values seem unrealistic
print(f"\n📈 BASIC STATISTICS (for number columns):")
print(df.describe())


# --- STEP 7: MISSING VALUES CHECK ---
# .isnull() marks True wherever a cell is empty
# .sum() counts how many True values per column
missing = df.isnull().sum()
missing_percent = (df.isnull().sum() / len(df)) * 100
# We calculate percentage too — e.g., "30% of BUILDUP AREA is missing"

print(f"\n🕳️  MISSING VALUES PER COLUMN:")
missing_report = pd.DataFrame({
    'Missing Count': missing,
    'Missing Percent (%)': missing_percent.round(2)
})
print(missing_report[missing_report['Missing Count'] > 0])  # Only show columns WITH missing values
# If nothing prints here, all columns are complete — great!


# --- STEP 8: UNIQUE VALUES IN CATEGORICAL COLUMNS ---
# For text columns, let's see what unique values exist
# This helps us understand variety in location, facing direction, etc.

print(f"\n🏷️  UNIQUE VALUES IN KEY COLUMNS:")

categorical_cols = ['FACING', 'ROAD ACCESS']  # Text columns we want to explore

for col in categorical_cols:
    if col in df.columns:
        unique_vals = df[col].value_counts()
        print(f"\n  📌 {col} ({df[col].nunique()} unique values):")
        print(unique_vals.head(10).to_string())  # Show top 10 most common values
        # .value_counts() sorts by most frequent first


# --- STEP 9: SAMPLE OF LOCATION COLUMN ---
# Location is complex — let's see some examples
print(f"\n📍 SAMPLE LOCATION VALUES (first 15):")
print(df['LOCATION'].head(15).to_string())

# --- STEP 10: SAMPLE OF PRICE COLUMN ---
# Let's see how prices are stored
print(f"\n💰 SAMPLE PRICE VALUES (first 10):")
print(df['PRICE'].head(10).to_string())


# --- STEP 11: SAMPLE OF AMENITIES COLUMN ---
print(f"\n🏠 SAMPLE AMENITIES VALUES (first 5):")
print(df['AMENITIES'].head(5).to_string())


# --- STEP 12: DUPLICATE ROWS CHECK ---
duplicates = df.duplicated().sum()
print(f"\n🔄 DUPLICATE ROWS: {duplicates}")
# If this is > 0, we have exact duplicate listings we'll remove in Phase 3


# --- FINAL SUMMARY ---
print("\n" + "=" * 60)
print("📊 PHASE 2 SUMMARY")
print("=" * 60)
print(f"Total houses in dataset : {rows}")
print(f"Total features          : {columns}")
print(f"Missing value columns   : {(missing > 0).sum()}")
print(f"Duplicate rows          : {duplicates}")
print(f"Target variable         : PRICE")
print(f"Type of problem         : Regression (predicting a number)")
print("=" * 60)
