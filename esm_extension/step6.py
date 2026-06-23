import pandas as pd
import pickle
import ast
import networkx as nx

kg = pickle.load(open('data/processed/kg.pkl', 'rb'))
predictions = pd.read_csv("esm_extension/drug_protein_predictions.csv")
novel_preds = pd.read_csv("data/processed/novel_predictions.csv")
gene_names = pd.read_csv("data/raw/gene_names.tsv", sep='\t')
disease_names = pd.read_csv("data/processed/disease_names.csv")

disease_name_map = dict(zip(disease_names.iloc[:,0], disease_names.iloc[:,1]))

uniprot_to_ensg = {}
for _, row in gene_names.iterrows():
    if pd.isna(row['uniprot_ids']) or pd.isna(row['ensembl_gene_id']):
        continue
    try:
        for u in ast.literal_eval(row['uniprot_ids']):
            uniprot_to_ensg[u] = row['ensembl_gene_id']
    except:
        pass

print("=== Mechanistic Paths: Drug → Protein → Disease ===\n")
results = []

for _, row in predictions.iterrows():
    drug_name = row['drug_name']
    protein = row['predicted_target_uniprot']
    gene = row['predicted_target_gene']
    repurposing_disease = row['disease_name']
    binding_score = row['binding_score']

    ensg = uniprot_to_ensg.get(protein)
    if not ensg or ensg not in kg:
        continue

    # Get diseases this protein's gene is associated with
    disease_neighbors = list(kg.successors(ensg))
    if not disease_neighbors:
        continue

    for disease_id in disease_neighbors:
        disease_label = disease_name_map.get(disease_id, disease_id)
        print(f"{drug_name} → {gene} ({protein}) → {disease_label}")
        print(f"  Repurposing target: {repurposing_disease}")
        print(f"  Binding score: {binding_score:.4f}")
        print(f"  Mechanistic link: {ensg} → {disease_id}\n")
        results.append({
            'drug_name': drug_name,
            'predicted_target_uniprot': protein,
            'predicted_target_gene': gene,
            'ensembl_id': ensg,
            'mechanistic_disease': disease_label,
            'mechanistic_disease_id': disease_id,
            'repurposing_disease': repurposing_disease,
            'binding_score': binding_score
        })

out = pd.DataFrame(results)
out.to_csv("esm_extension/mechanistic_paths.csv", index=False)
print(f"Total mechanistic links found: {len(results)}")
print("Saved to esm_extension/mechanistic_paths.csv")