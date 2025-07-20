import pandas as pd, sqlite3, pathlib

CSV = r"C:\Users\huynha8\Downloads\git_workshop\car-reference-db\data\vehicles_final_cleaned.csv"
DB  = pathlib.Path("db") / "car_reference.db"

df = pd.read_csv(CSV)
df = df.rename(columns={
    "manufacturer": "make",
    "odometer": "mileage_km"
})[["id", "make", "model", "year", "price", "mileage_km", "created_at"]]

before = len(df)

# ---------- data cleaning ----------
df = df.dropna(subset=["make"])           # keep rows that have a make
df = df.dropna(subset=["year"])           # keep rows that have a year
df["year"] = df["year"].astype(int)       # force to int; will raise on bad strings
# ------------------------------------

print(f"Imported {len(df):,} rows (dropped {before-len(df):,} bad rows).")

with sqlite3.connect(DB) as con:
    con.execute("DELETE FROM vehicle_listings")        # wipe old rows
    df.to_sql("vehicle_listings", con, if_exists="append", index=False)

print("Imported", len(df), "rows.")