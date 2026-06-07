# src/check_kg.py
import pickle
import pandas as pd

# Load graph
with open("data/processed/kg.pkl", "rb") as f:
    G = pickle.load(f)

print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")

# Check Ibuprofen
if 'CHEMBL521' in G:
    neighbors = list(G.successors('CHEMBL521'))
    print(f"\nIbuprofen (CHEMBL521) targets: {neighbors[:5]}")
else:
    print("\nCHEMBL521 not found")

# Degree distribution
degrees = [d for n, d in G.degree()]
print(f"\nMax degree: {max(degrees)}")
print(f"Mean degree: {sum(degrees)/len(degrees):.2f}")
print(f"Nodes with degree 1: {sum(1 for d in degrees if d == 1)}")

# Sample disease
gene_disease = pd.read_csv("data/processed/gene_disease.csv")
diseases = set(gene_disease['diseaseId'])
sample_disease = list(diseases)[0]
print(f"\nSample disease: {sample_disease}")
print(f"Genes associated: {list(G.predecessors(sample_disease))[:5]}")