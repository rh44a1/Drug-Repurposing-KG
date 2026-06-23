import pandas as pd
import os

# Load all 8 parts
parts = []
for i in range(8):
    path = f"data/raw/opentargets_part{i}.parquet"
    if os.path.exists(path):
        df = pd.read_parquet(path, columns=["diseaseId", "targetId", "associationScore"])
        parts.append(df)
        print(f"Loaded part {i}: {len(df)} rows")

ot = pd.concat(parts, ignore_index=True)
print(f"\nTotal before filter: {len(ot)}")

# Filter high confidence
ot = ot[ot["associationScore"] >= 0.5]
print(f"After score >= 0.5: {len(ot)}")
print(f"Unique genes: {ot['targetId'].nunique()}")
print(f"Unique diseases: {ot['diseaseId'].nunique()}")

# Save gene_disease
ot.to_csv("data/processed/gene_disease.csv", index=False)
print("Saved gene_disease.csv")

# Fetch disease names for all unique disease IDs
import requests
import time

unique_diseases = ot['diseaseId'].unique().tolist()
print(f"\nFetching names for {len(unique_diseases)} diseases...")

disease_names = {}
for i, disease_id in enumerate(unique_diseases):
    url = f"https://www.ebi.ac.uk/ols4/api/terms?id={disease_id}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        terms = data.get('_embedded', {}).get('terms', [])
        if terms:
            disease_names[disease_id] = terms[0].get('label', 'Unknown')
        else:
            disease_names[disease_id] = 'Unknown'
    except:
        disease_names[disease_id] = 'Unknown'
    if i % 50 == 0:
        print(f"  {i}/{len(unique_diseases)}")
    time.sleep(0.2)

mapping_df = pd.DataFrame(list(disease_names.items()), 
                          columns=['disease_id', 'disease_name'])
mapping_df = mapping_df[mapping_df['disease_name'] != 'Unknown']
mapping_df.to_csv("data/processed/disease_names.csv", index=False)
print(f"Saved {len(mapping_df)} disease names.")