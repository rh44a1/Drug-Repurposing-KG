import pandas as pd
import requests
import time

scores_df = pd.read_csv("data/processed/jaccard_baseline.csv")
unique_diseases = scores_df['disease'].unique().tolist()
print(f"Decoding {len(unique_diseases)} diseases...")

def fetch_disease_name(disease_id):
    # Convert underscore format to colon format for API queries
    colon_id = disease_id.replace('_', ':', 1)  # MONDO_0018240 → MONDO:0018240
    
    # Strategy 1: OLS4 search by short_form (handles underscore format natively)
    try:
        url = f"https://www.ebi.ac.uk/ols4/api/terms?short_form={disease_id}"
        r = requests.get(url, timeout=10)
        data = r.json()
        terms = data.get('_embedded', {}).get('terms', [])
        if terms:
            return terms[0].get('label', None)
    except:
        pass

    # Strategy 2: OLS4 with colon format
    try:
        url = f"https://www.ebi.ac.uk/ols4/api/terms?id={colon_id}"
        r = requests.get(url, timeout=10)
        data = r.json()
        terms = data.get('_embedded', {}).get('terms', [])
        if terms:
            return terms[0].get('label', None)
    except:
        pass

    # Strategy 3: OLS4 search endpoint (broader, catches edge cases)
    try:
        url = f"https://www.ebi.ac.uk/ols4/api/search?q={colon_id}&exact=true&queryFields=obo_id"
        r = requests.get(url, timeout=10)
        data = r.json()
        docs = data.get('response', {}).get('docs', [])
        if docs:
            return docs[0].get('label', None)
    except:
        pass

    return 'Unknown'

disease_names = {}
for i, disease_id in enumerate(unique_diseases):
    disease_names[disease_id] = fetch_disease_name(disease_id)
    
    if i % 50 == 0:
        resolved = sum(1 for v in disease_names.values() if v != 'Unknown')
        print(f"  {i}/{len(unique_diseases)} — resolved {resolved} so far")
    
    time.sleep(0.2)

mapping_df = pd.DataFrame(list(disease_names.items()), columns=['disease_id', 'disease_name'])
mapping_df.to_csv("data/processed/disease_names.csv", index=False)

resolved = (mapping_df['disease_name'] != 'Unknown').sum()
print(f"Saved {len(mapping_df)} entries. Resolved: {resolved}, Unknown: {len(mapping_df) - resolved}")