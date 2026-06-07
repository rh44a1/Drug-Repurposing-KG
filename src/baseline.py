import pandas as pd
import ast
from collections import defaultdict

# Load data
drug_target = pd.read_csv("data/processed/drug_target.csv")
gene_disease = pd.read_csv("data/processed/gene_disease.csv")
hgnc = pd.read_csv("data/raw/gene_names.tsv", sep='\t')

# Build UniProt -> Ensembl mapping from HGNC
hgnc = hgnc[hgnc['ensembl_gene_id'].notna() & hgnc['uniprot_ids'].notna()]

def extract_uniprot(val):
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[0]
    except:
        return None

hgnc['uniprot_id'] = hgnc['uniprot_ids'].apply(extract_uniprot)
hgnc = hgnc[hgnc['uniprot_id'].notna()]
uniprot_to_ensg = dict(zip(hgnc['uniprot_id'], hgnc['ensembl_gene_id']))
print(f"UniProt->Ensembl mapping: {len(uniprot_to_ensg)} entries")

# Map drug targets from UniProt to Ensembl
drug_target['ensg_id'] = drug_target['uniprot_id'].map(uniprot_to_ensg)
drug_target_mapped = drug_target[drug_target['ensg_id'].notna()]
print(f"Drug-target rows with Ensembl mapping: {len(drug_target_mapped)}")

# Build drug -> set of Ensembl gene targets
drug_targets = defaultdict(set)
for _, row in drug_target_mapped.iterrows():
    drug_targets[row['drug_id']].add(row['ensg_id'])

# Build Ensembl gene -> set of diseases
gene_diseases = defaultdict(set)
for _, row in gene_disease.iterrows():
    gene_diseases[row['targetId']].add(row['diseaseId'])

# Compute drug-disease scores
print("Computing Jaccard scores...")
drug_disease_scores = []
drugs = list(drug_targets.keys())

for drug in drugs:
    targets = drug_targets[drug]
    connected_diseases = set()
    for t in targets:
        connected_diseases.update(gene_diseases.get(t, set()))
    
    for disease in connected_diseases:
        connecting = [t for t in targets if disease in gene_diseases.get(t, set())]
        score = len(connecting) / len(targets)
        drug_disease_scores.append({
            'drug': drug,
            'disease': disease,
            'jaccard_score': score,
            'n_connecting_targets': len(connecting)
        })

scores_df = pd.DataFrame(drug_disease_scores)
print(f"Drug-disease pairs scored: {len(scores_df)}")
print(f"Unique drugs: {scores_df['drug'].nunique()}")
print(f"Unique diseases: {scores_df['disease'].nunique()}")
print("\nTop 10 predictions:")
print(scores_df.sort_values('jaccard_score', ascending=False).head(10))

scores_df.to_csv("data/processed/jaccard_baseline.csv", index=False)
print("\nSaved to data/processed/jaccard_baseline.csv")