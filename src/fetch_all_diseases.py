import requests
import pandas as pd

print("Fetching MONDO diseases via OBO API...")

# Download MONDO disease list directly from their GitHub releases
url = "https://raw.githubusercontent.com/monarch-initiative/mondo/master/src/ontology/subsets/mondo-rare.obo"
r = requests.get(url, timeout=60)

lines = r.text.split('\n')
diseases = []
current_id = None
current_name = None

for line in lines:
    if line.startswith('id: MONDO:'):
        current_id = line.replace('id: ', '').strip().replace('MONDO:', 'MONDO_')
    elif line.startswith('name:'):
        current_name = line.replace('name: ', '').strip()
    elif line == '' and current_id and current_name:
        diseases.append({'id': current_id, 'name': current_name})
        current_id = None
        current_name = None

df = pd.DataFrame(diseases)
print(f"Total: {len(df)} MONDO diseases")
print(df.head(10))
df.to_csv("data/processed/disease_names_full.csv", index=False)
print("Saved.")