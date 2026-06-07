import pandas as pd
import torch
import numpy as np
from pykeen.triples import TriplesFactory

# Load mappings
drug_map = pd.read_csv("data/processed/dc_drug_chembl_map.csv")
disease_map = pd.read_csv("data/processed/dc_disease_map.csv")
test_df = pd.read_csv("data/processed/dc_test.csv")

# Merge mappings
test_df = test_df.merge(drug_map, on='drug_name', how='left')
test_df = test_df.merge(
    disease_map[['dc_disease_name', 'onto_id']].rename(columns={'dc_disease_name': 'disease_name'}),
    on='disease_name', how='left'
)
test_mapped = test_df[test_df['chembl_id'].notna() & test_df['onto_id'].notna()].copy()
print(f"Evaluatable test pairs: {len(test_mapped)}")

# Load model and triples
print("Loading RotatE model...")
model = torch.load("models/content/RotatE/trained_model.pkl", 
                   map_location='cpu', weights_only=False)
model.eval()
tf = TriplesFactory.from_path_binary("data/processed/splits/training")
entity_to_id = tf.entity_to_id
relation_to_id = tf.relation_to_id

print(f"Entities in KG: {len(entity_to_id)}")
print(f"Relations: {list(relation_to_id.keys())}")

# Load drug_target to try name-based fallback
drug_target = pd.read_csv("data/processed/drug_target.csv")
name_to_chembl = dict(zip(
    drug_target['drug_name'].str.upper(),
    drug_target['drug_id']
))

# Score pairs
results = []
missing_drug = 0
missing_disease = 0

assoc_rel_id = relation_to_id.get('ASSOCIATED_WITH', None)
if assoc_rel_id is None:
    print("ERROR: ASSOCIATED_WITH relation not found")
    print("Available relations:", list(relation_to_id.keys()))

for _, row in test_mapped.iterrows():
    drug_id = row['chembl_id']
    disease_id = row['onto_id']
    
    # Try ChEMBL ID first, fallback to drug name lookup
    if drug_id not in entity_to_id:
        fallback = name_to_chembl.get(str(row['drug_name']).upper())
        if fallback and fallback in entity_to_id:
            drug_id = fallback
        else:
            missing_drug += 1
            continue
    
    if disease_id not in entity_to_id:
        missing_disease += 1
        continue
    
    with torch.no_grad():
        score = model.score_hrt(torch.tensor([[
            entity_to_id[drug_id],
            assoc_rel_id,
            entity_to_id[disease_id]
        ]]))
    
    results.append({
        'Drug': row['drug_name'].title(),
        'Disease': row['disease_name'],
        'ChEMBL ID': drug_id,
        'Disease ID': disease_id,
        'Raw Score': score.item()
    })

print(f"\nScored: {len(results)} pairs")
print(f"Missing drugs: {missing_drug}")
print(f"Missing diseases: {missing_disease}")

# Normalize scores to 0-1 (higher = better)
results_df = pd.DataFrame(results)
if len(results_df) > 0:
    min_s = results_df['Raw Score'].min()
    max_s = results_df['Raw Score'].max()
    results_df['Confidence'] = ((results_df['Raw Score'] - min_s) / (max_s - min_s)).round(3)
    results_df = results_df.drop(columns=['Raw Score'])
    results_df = results_df.sort_values('Confidence', ascending=False).reset_index(drop=True)
    
    print("\n" + "="*70)
    print(f"{'ROTATЕ EVALUATION RESULTS — DrugCentral Test Set (2021+)':^70}")
    print("="*70)
    print(f"{'#':<4} {'Drug':<25} {'Disease':<30} {'Conf':>6}")
    print("-"*70)
    for i, row in results_df.iterrows():
        print(f"{i+1:<4} {row['Drug']:<25} {row['Disease']:<30} {row['Confidence']:>6.3f}")
    print("="*70)
    
    results_df.to_csv("data/processed/evaluation_results.csv", index=False)
    print(f"\nSaved {len(results_df)} results.")