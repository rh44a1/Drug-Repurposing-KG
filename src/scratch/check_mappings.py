import pandas as pd

# Load mappings
drug_map = pd.read_csv("data/processed/dc_drug_chembl_map.csv")
disease_map = pd.read_csv("data/processed/dc_disease_map.csv")
test_df = pd.read_csv("data/processed/dc_test.csv")

print("Drug map columns:", drug_map.columns.tolist())
print("Disease map columns:", disease_map.columns.tolist())
print("Test df columns:", test_df.columns.tolist())
print()
print(drug_map.head(3))
print(disease_map.head(3))
print(test_df.head(3))