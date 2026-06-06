import pandas as pd

data = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\cleaned_house_data.csv")

location_map = data.groupby("LOCATION")["PRICE"].median().reset_index()
location_map.columns = ["location", "encoded"]
location_map = location_map.sort_values("location")

print(location_map.to_string(index=False))