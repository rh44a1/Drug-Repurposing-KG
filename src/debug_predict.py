import pandas as pd
import ast
from pykeen.triples import TriplesFactory

drug_target = pd.read_csv("data/processed/drug_target.csv")
gene_disease = pd.read_csv("data/processed/gene_disease.csv")
hgnc = pd.read_csv("data/raw/gene_names.tsv", sep='\t')

def extract_uniprot(val):
    try:
        parsed = ast.literal_eval(val)
        return parsed[0] if parsed else None
    except:
        return None

hgnc = hgnc[hgnc['ensembl_gene_id'].notna() & hgnc['uniprot_ids'].notna()]
hgnc['uniprot_id'] = hgnc['uniprot_ids'].apply(extract_uniprot)
uniprot_to_ensg = dict(zip(hgnc['uniprot_id'], hgnc['ensembl_gene_id']))

drug_to_proteins = {}
for _, row in drug_target.iterrows():
    d = row['drug_id']
    if d not in drug_to_proteins:
        drug_to_proteins[d] = []
    drug_to_proteins[d].append(row['uniprot_id'])

protein_to_diseases = {}
for _, row in gene_disease.iterrows():
    g = row['targetId']
    if g not in protein_to_diseases:
        protein_to_diseases[g] = []
    protein_to_diseases[g].append((row['diseaseId'], row['associationScore']))

known_drug_disease = set()
for drug, proteins in drug_to_proteins.items():
    for p in proteins:
        ensg = uniprot_to_ensg.get(p)
        if ensg:
            for disease, _ in protein_to_diseases.get(ensg, []):
                known_drug_disease.add((drug, disease))

print(f"Known drug-disease pairs: {len(known_drug_disease)}")

# Check ibuprofen specifically
test_pairs = [(k, v) for k, v in known_drug_disease if k == 'CHEMBL521']
print(f"Known pairs for CHEMBL521: {len(test_pairs)}")
print(test_pairs[:5])

# Check how many total drug-disease combos exist
total_possible = 0
for drug, proteins in drug_to_proteins.items():
    diseases_seen = set()
    for p in proteins:
        ensg = uniprot_to_ensg.get(p)
        if ensg:
            for disease, _ in protein_to_diseases.get(ensg, []):
                diseases_seen.add(disease)
    total_possible += len(diseases_seen)

print(f"Total possible drug-disease pairs: {total_possible}")
print(f"Known (excluded): {len(known_drug_disease)}")
print(f"Novel (remaining): {total_possible - len(known_drug_disease)}")