# src/map_diseases_umls_to_mondo.py
import pandas as pd
import requests
import io

train_df = pd.read_csv("data/processed/dc_train.csv")
test_df  = pd.read_csv("data/processed/dc_test.csv")
all_df   = pd.concat([train_df, test_df])
unique_cuis = set(all_df['umls_cui'].dropna().unique())
print(f"Need to map {len(unique_cuis)} UMLS CUIs...")

# Download official MONDO→UMLS exact match mapping file (~16k mappings)
url = "https://raw.githubusercontent.com/monarch-initiative/mondo/master/src/ontology/mappings/mondo_exactmatch_umls.sssom.tsv"
print("Downloading MONDO UMLS mappings...")
r = requests.get(url, timeout=30)

# Skip comment lines starting with #
lines = [l for l in r.text.splitlines() if not l.startswith('#')]
mapping_df = pd.read_csv(io.StringIO('\n'.join(lines)), sep='\t')

# mapping_df has: subject_id (MONDO:xxx), object_id (UMLS:Cxxx)
# Flip to UMLS→MONDO, clean up format to match your KG (MONDO_xxx)
mapping_df['umls_cui']     = mapping_df['object_id'].str.replace('UMLS:', '', regex=False)
mapping_df['kg_disease_id'] = mapping_df['subject_id'].str.replace(':', '_', regex=False)

umls_to_mondo = dict(zip(mapping_df['umls_cui'], mapping_df['kg_disease_id']))
print(f"Loaded {len(umls_to_mondo)} UMLS→MONDO mappings from official file")

# Apply to your CUIs
disease_map = {cui: umls_to_mondo.get(cui, None) for cui in unique_cuis}
matched = sum(1 for v in disease_map.values() if v)
print(f"Matched {matched}/{len(unique_cuis)} ({100*matched/len(unique_cuis):.1f}%)")

dis_df = pd.DataFrame(list(disease_map.items()), columns=['umls_cui', 'kg_disease_id'])
dis_df.to_csv("data/processed/dc_disease_mondo_map.csv", index=False)
print("Saved to data/processed/dc_disease_mondo_map.csv")