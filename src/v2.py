# src/map_diseases_umls_to_mondo_v2.py
import pandas as pd
import requests
import io
import time

train_df = pd.read_csv("data/processed/dc_train.csv")
test_df  = pd.read_csv("data/processed/dc_test.csv")
all_df   = pd.concat([train_df, test_df])

existing    = pd.read_csv("data/processed/dc_disease_mondo_map.csv")
unmatched   = existing[existing['kg_disease_id'].isna()]['umls_cui'].tolist()
cui_to_name = dict(zip(all_df['umls_cui'], all_df['disease_name']))
print(f"Already matched: {existing['kg_disease_id'].notna().sum()}, recovering {len(unmatched)}...")

# ── Strategy 2: hasDbXref file (broader than exactmatch) ────────────────────
url = "https://raw.githubusercontent.com/monarch-initiative/mondo/master/src/ontology/mappings/mondo_hasdbxref_umls.sssom.tsv"
r = requests.get(url, timeout=30)
lines = [l for l in r.text.splitlines() if not l.startswith('#')]
xref_df = pd.read_csv(io.StringIO('\n'.join(lines)), sep='\t')
xref_df['umls_cui']      = xref_df['object_id'].str.replace('UMLS:', '', regex=False)
xref_df['kg_disease_id'] = xref_df['subject_id'].str.replace(':', '_', regex=False)
xref_map = dict(zip(xref_df['umls_cui'], xref_df['kg_disease_id']))

still_unmatched = []
xref_recovered = 0
for cui in unmatched:
    if cui in xref_map:
        existing.loc[existing['umls_cui'] == cui, 'kg_disease_id'] = xref_map[cui]
        xref_recovered += 1
    else:
        still_unmatched.append(cui)
print(f"hasDbXref recovered: {xref_recovered}, still unmatched: {len(still_unmatched)}")

# ── Strategy 3: OLS4 label search by disease name ───────────────────────────
name_recovered = 0
for i, cui in enumerate(still_unmatched):
    name = cui_to_name.get(cui)
    if not name or str(name) == 'nan':
        continue
    try:
        url = f"https://www.ebi.ac.uk/ols4/api/search?q={requests.utils.quote(str(name))}&ontology=mondo&exact=true&limit=1"
        r = requests.get(url, timeout=10)
        docs = r.json().get('response', {}).get('docs', [])
        if docs:
            obo_id = docs[0].get('obo_id', '')
            if obo_id.startswith('MONDO'):
                existing.loc[existing['umls_cui'] == cui, 'kg_disease_id'] = obo_id.replace(':', '_')
                name_recovered += 1
        time.sleep(0.1)
    except:
        pass
    if i % 100 == 0:
        print(f"  name search {i}/{len(still_unmatched)}, recovered {name_recovered} so far")

print(f"Name search recovered: {name_recovered}")

existing.to_csv("data/processed/dc_disease_mondo_map.csv", index=False)
total = existing['kg_disease_id'].notna().sum()
print(f"\nFinal: {total}/{len(existing)} matched ({100*total/len(existing):.1f}%)")