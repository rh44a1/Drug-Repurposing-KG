import pandas as pd
import networkx as nx
import pickle
import os

# Load all processed files
drug_target = pd.read_csv("data/processed/drug_target.csv")
stitch = pd.read_csv("data/processed/stitch.csv")
gene_disease = pd.read_csv("data/processed/gene_disease.csv")
ppi = pd.read_csv("data/processed/protein_protein.csv")

# Build unified triples dataframe
triples = []

# Drug -> TARGETS -> Protein
for _, row in drug_target.iterrows():
    triples.append({
        'head': row['drug_id'],
        'relation': 'TARGETS',
        'tail': row['uniprot_id'],
        'weight': row['pchembl_value'] / 10.0  # normalize to 0-1
    })

# Chemical -> INTERACTS_WITH -> Protein (STITCH)
for _, row in stitch.iterrows():
    triples.append({
        'head': row['chemical'],
        'relation': 'INTERACTS_WITH',
        'tail': row['protein'].replace('9606.', ''),
        'weight': row['combined_score'] / 1000.0  # normalize to 0-1
    })

# Gene -> ASSOCIATED_WITH -> Disease
for _, row in gene_disease.iterrows():
    triples.append({
        'head': row['targetId'],
        'relation': 'ASSOCIATED_WITH',
        'tail': row['diseaseId'],
        'weight': row['associationScore']  # already 0-1
    })

# Protein -> INTERACTS_WITH -> Protein (STRING)
for _, row in ppi.iterrows():
    triples.append({
        'head': row['protein1'].replace('9606.', ''),
        'relation': 'PPI',
        'tail': row['protein2'].replace('9606.', ''),
        'weight': row['combined_score'] / 1000.0
    })

df_triples = pd.DataFrame(triples)
print(f"Total triples: {len(df_triples)}")
print(f"Relation types: {df_triples['relation'].value_counts()}")
print(df_triples.head())

os.makedirs("data/processed", exist_ok=True)
df_triples.to_csv("data/processed/triples.csv", index=False)
print("Saved to data/processed/triples.csv")
# Build NetworkX graph
print("\nBuilding NetworkX graph...")
G = nx.MultiDiGraph()  # MultiDiGraph allows multiple edge types between same nodes

for _, row in df_triples.iterrows():
    G.add_edge(
        row['head'],
        row['tail'],
        relation=row['relation'],
        weight=row['weight']
    )

print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")

# Node type breakdown
drugs = set(drug_target['drug_id'])
chemicals = set(stitch['chemical'])
proteins_uniprot = set(drug_target['uniprot_id'])
proteins_ensp = set(ppi['protein1'].str.replace('9606.', '')).union(set(ppi['protein2'].str.replace('9606.', '')))
diseases = set(gene_disease['diseaseId'])
genes_ensembl = set(gene_disease['targetId'])

print(f"\nNode type estimates:")
print(f"  Drugs (ChEMBL): {len(drugs)}")
print(f"  Chemicals (STITCH): {len(chemicals)}")
print(f"  Proteins (UniProt): {len(proteins_uniprot)}")
print(f"  Proteins (ENSP): {len(proteins_ensp)}")
print(f"  Diseases: {len(diseases)}")
print(f"  Genes (Ensembl): {len(genes_ensembl)}")

# Save graph
with open("data/processed/kg.pkl", "wb") as f:
    pickle.dump(G, f)
print("\nGraph saved to data/processed/kg.pkl")