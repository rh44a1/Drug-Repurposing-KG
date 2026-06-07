import pandas as pd
import os

# Load all 3 parts
parts = []
for i in range(3):
    path = f"data/raw/opentargets_part{i}.parquet"
    df = pd.read_parquet(path, columns=["diseaseId", "targetId", "associationScore"])
    parts.append(df)

ot = pd.concat(parts, ignore_index=True)

# Filter to high confidence only
ot = ot[ot["associationScore"] >= 0.5]

print(f"Total associations: {len(ot)}")
print(f"Unique genes: {ot['targetId'].nunique()}")
print(f"Unique diseases: {ot['diseaseId'].nunique()}")
print(ot.head())

# Save
os.makedirs("data/processed", exist_ok=True)
ot.to_csv("data/processed/gene_disease.csv", index=False)
print("Saved to data/processed/gene_disease.csv")