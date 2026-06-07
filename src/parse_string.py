import pandas as pd
import os

# Load protein name mapping
print("Loading protein info...")
info = pd.read_csv("data/raw/9606.protein.info.v12.0.txt", sep='\t')
info = info.rename(columns={'#string_protein_id': 'string_id'})
info = info[['string_id', 'preferred_name', 'annotation']]

# Load protein-protein interactions
print("Loading STRING links...")
links = pd.read_csv("data/raw/9606.protein.links.v12.0.txt", sep=' ')
print(f"Raw shape: {links.shape}")

# Filter to high confidence
links_filtered = links[links['combined_score'] >= 700]
print(f"After score >= 700 filter: {links_filtered.shape}")

# Map protein IDs to gene names
links_filtered = links_filtered.merge(
    info.rename(columns={'string_id': 'protein1', 'preferred_name': 'gene1'}),
    on='protein1', how='left'
).merge(
    info.rename(columns={'string_id': 'protein2', 'preferred_name': 'gene2'}),
    on='protein2', how='left'
)

links_filtered = links_filtered[['protein1', 'gene1', 'protein2', 'gene2', 'combined_score']]

print(f"Unique proteins: {pd.concat([links_filtered['protein1'], links_filtered['protein2']]).nunique()}")
print(links_filtered.head())

os.makedirs("data/processed", exist_ok=True)
links_filtered.to_csv("data/processed/protein_protein.csv", index=False)
print("Saved to data/processed/protein_protein.csv")