import requests
import pandas as pd
import time

all_terms = []

# 1. MONDO (already have it)
mondo = pd.read_csv("data/processed/disease_names_full.csv")
all_terms.append(mondo)
print(f"MONDO: {len(mondo)}")

# 2. HP terms from OBO
print("Fetching HP terms...")
r = requests.get("https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo", timeout=60)
lines = r.text.split('\n')
current_id, current_name = None, None
hp_terms = []
for line in lines:
    if line.startswith('id: HP:'):
        current_id = line.replace('id: ', '').strip().replace('HP:', 'HP_')
    elif line.startswith('name:'):
        current_name = line.replace('name: ', '').strip()
    elif line == '' and current_id and current_name:
        hp_terms.append({'id': current_id, 'name': current_name})
        current_id, current_name = None, None
hp_df = pd.DataFrame(hp_terms)
print(f"HP: {len(hp_df)}")
all_terms.append(hp_df)

# 3. EFO terms from OBO
print("Fetching EFO terms...")
r = requests.get("https://github.com/EBISPOT/efo/releases/download/current/efo.obo", timeout=120)
lines = r.text.split('\n')
current_id, current_name = None, None
efo_terms = []
for line in lines:
    if line.startswith('id: EFO:'):
        current_id = line.replace('id: ', '').strip().replace('EFO:', 'EFO_')
    elif line.startswith('name:'):
        current_name = line.replace('name: ', '').strip()
    elif line == '' and current_id and current_name:
        efo_terms.append({'id': current_id, 'name': current_name})
        current_id, current_name = None, None
efo_df = pd.DataFrame(efo_terms)
print(f"EFO: {len(efo_df)}")
all_terms.append(efo_df)

# Combine all
combined = pd.concat(all_terms).drop_duplicates(subset='name')
print(f"Combined: {len(combined)} terms")
combined.to_csv("data/processed/disease_names_full.csv", index=False)
print("Saved.")