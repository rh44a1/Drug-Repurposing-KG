import pandas as pd
import os

print("Loading STITCH...")
df = pd.read_csv(
    "data/raw/9606.protein_chemical.links.detailed.v5.0.tsv",
    sep='\t'
)

print(f"Raw shape: {df.shape}")
print(df.head())
print(df.columns.tolist())

# Filter to high confidence only
df_filtered = df[df['combined_score'] >= 700]

print(f"After score >= 700 filter: {df_filtered.shape}")
print(f"Unique chemicals: {df_filtered['chemical'].nunique()}")
print(f"Unique proteins: {df_filtered['protein'].nunique()}")

os.makedirs("data/processed", exist_ok=True)
df_filtered.to_csv("data/processed/stitch.csv", index=False)
print("Saved to data/processed/stitch.csv")