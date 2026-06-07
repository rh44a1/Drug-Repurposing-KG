import pandas as pd
from rapidfuzz import process, fuzz
from pykeen.triples import TriplesFactory

# Load only disease IDs that actually exist in KG
tf = TriplesFactory.from_path_binary("data/processed/splits/training")
entity_to_id = tf.entity_to_id

kg_disease_ids = set(e for e in entity_to_id.keys()
                     if e.startswith('EFO_') or e.startswith('MONDO_')
                     or e.startswith('HP_') or e.startswith('Orphanet_'))

# Load disease names and filter to KG diseases only
disease_names = pd.read_csv("data/processed/disease_names.csv")
disease_names = disease_names[disease_names['disease_id'].isin(kg_disease_ids)]
disease_names = disease_names[~disease_names['disease_name'].str.startswith('obsolete_')]
print(f"KG diseases with names: {len(disease_names)}")

# Load DrugCentral diseases
train_df = pd.read_csv("data/processed/dc_train.csv")
test_df = pd.read_csv("data/processed/dc_test.csv")
dc_diseases = pd.concat([train_df, test_df])['disease_name'].dropna().unique().tolist()
print(f"DrugCentral unique diseases: {len(dc_diseases)}")

# Fuzzy match against KG disease names
onto_names = disease_names['disease_name'].str.lower().tolist()
onto_ids = disease_names['disease_id'].tolist()
onto_names_original = disease_names['disease_name'].tolist()

matches = []
for i, dc_name in enumerate(dc_diseases):
    dc_lower = dc_name.lower()
    
    # Exact match first
    if dc_lower in onto_names:
        idx = onto_names.index(dc_lower)
        matches.append({
            'dc_disease_name': dc_name,
            'onto_name': onto_names_original[idx],
            'onto_id': onto_ids[idx],
            'similarity': 100.0,
            'match_type': 'exact'
        })
        continue
    
    # Fuzzy match
    threshold = 75 if len(dc_name) > 20 else 82
    result = process.extractOne(dc_lower, onto_names, scorer=fuzz.token_sort_ratio)
    if result and result[1] >= threshold:
        idx = onto_names.index(result[0])
        matches.append({
            'dc_disease_name': dc_name,
            'onto_name': onto_names_original[idx],
            'onto_id': onto_ids[idx],
            'similarity': result[1],
            'match_type': 'fuzzy'
        })
    
    if i % 200 == 0:
        print(f"  {i}/{len(dc_diseases)}")

matches_df = pd.DataFrame(matches)
exact = len(matches_df[matches_df['match_type'] == 'exact'])
fuzzy = len(matches_df[matches_df['match_type'] == 'fuzzy'])
print(f"\nExact: {exact}, Fuzzy: {fuzzy}")
print(f"Total: {len(matches_df)}/{len(dc_diseases)} ({100*len(matches_df)/len(dc_diseases):.1f}%)")
print(matches_df.head(10))

matches_df.to_csv("data/processed/dc_disease_map.csv", index=False)
print("Saved.")