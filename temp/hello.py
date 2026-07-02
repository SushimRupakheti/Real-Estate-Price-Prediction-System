import sqlite3
import os

base_dir = os.path.dirname(__file__)
db_path = os.path.abspath(os.path.join(base_dir, "..", "src", "backend", "predictions.db"))

print(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()