import requests
import pandas as pd

url = 'https://rest.genenames.org/fetch/status/Approved'
headers = {'Accept': 'application/json'}

print("Fetching from HGNC API...")
r = requests.get(url, headers=headers)
data = r.json()

docs = data['response']['docs']
df = pd.DataFrame(docs)

# Add 'name' to the columns we keep
cols = [c for c in ['hgnc_id', 'symbol', 'name', 'ensembl_gene_id', 'entrez_id', 'uniprot_ids'] if c in df.columns]
df = df[cols]
df = df[df['ensembl_gene_id'].notna()]

print(f"With Ensembl IDs: {len(df)}")
print(df.head())

df.to_csv("data/raw/gene_names.tsv", sep='\t', index=False)
print("Saved.")