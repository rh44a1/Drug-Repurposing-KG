import pandas as pd
import torch
import ast
from pykeen.triples import TriplesFactory

print("Loading RotatE...")
model = torch.load("models/content/RotatE/trained_model.pkl",
                   map_location='cpu', weights_only=False)
model.eval()

tf = TriplesFactory.from_path_binary("data/processed/splits/training")
entity_to_id = tf.entity_to_id
relation_to_id = tf.relation_to_id

# Load data
drug_target = pd.read_csv("data/processed/drug_target.csv")
gene_disease = pd.read_csv("data/processed/gene_disease.csv")
ppi = pd.read_csv("data/processed/protein_protein.csv")
disease_names = pd.read_csv("data/processed/disease_names.csv")
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
ensg_to_uniprot = dict(zip(hgnc['ensembl_gene_id'], hgnc['uniprot_id']))

# Name maps
disease_name_map = dict(zip(disease_names['disease_id'], disease_names['disease_name']))
drug_name_map = dict(zip(drug_target['drug_id'], drug_target['drug_name']))

# Build lookups
drug_to_proteins = {}
for _, row in drug_target.iterrows():
    d = row['drug_id']
    if d not in drug_to_proteins:
        drug_to_proteins[d] = []
    drug_to_proteins[d].append(row['uniprot_id'])

# PPI: protein -> interacting proteins (using gene names)
gene_to_interactors = {}
for _, row in ppi.iterrows():
    g1 = row['gene1']
    g2 = row['gene2']
    if g1 not in gene_to_interactors:
        gene_to_interactors[g1] = []
    gene_to_interactors[g1].append(g2)

# Gene symbol -> Ensembl
hgnc_symbol_to_ensg = dict(zip(hgnc['symbol'] if 'symbol' in hgnc.columns else [], 
                                hgnc['ensembl_gene_id'] if 'ensembl_gene_id' in hgnc.columns else []))

gene_disease_map = {}
for _, row in gene_disease.iterrows():
    g = row['targetId']
    if g not in gene_disease_map:
        gene_disease_map[g] = []
    gene_disease_map[g].append((row['diseaseId'], row['associationScore']))

# Known drug-disease (2-hop) to exclude
known_pairs = set()
for drug, proteins in drug_to_proteins.items():
    for p in proteins:
        ensg = uniprot_to_ensg.get(p)
        if ensg:
            for disease, _ in gene_disease_map.get(ensg, []):
                known_pairs.add((drug, disease))

print(f"Known pairs to exclude: {len(known_pairs)}")

# Load HGNC symbol mapping
hgnc_df = pd.read_csv("data/raw/gene_names.tsv", sep='\t')
symbol_to_ensg = dict(zip(hgnc_df['symbol'], hgnc_df['ensembl_gene_id']))

# 3-hop scoring
targets_id = relation_to_id['TARGETS']
ppi_id = relation_to_id['PPI']
assoc_id = relation_to_id['ASSOCIATED_WITH']

print("Generating 3-hop predictions...")
all_predictions = []
drugs = [d for d in list(drug_to_proteins.keys())[:3000] if d in entity_to_id]

for i, drug in enumerate(drugs):
    drug_idx = entity_to_id[drug]
    disease_scores = {}

    for protein in drug_to_proteins[drug]:
        if protein not in entity_to_id:
            continue
        protein_idx = entity_to_id[protein]

        # Score drug -> protein
        with torch.no_grad():
            s1 = model.score_hrt(torch.tensor([[
                drug_idx, targets_id, protein_idx]])).item()

        # Get gene symbol for this protein
        ensg = uniprot_to_ensg.get(protein)
        if not ensg:
            continue
        gene_symbol = hgnc_df[hgnc_df['ensembl_gene_id'] == ensg]['symbol'].values
        if len(gene_symbol) == 0:
            continue
        gene_symbol = gene_symbol[0]

        # Get interacting proteins (PPI neighbors)
        interactors = gene_to_interactors.get(gene_symbol, [])[:10]  # top 10 interactors

        for interactor_symbol in interactors:
            interactor_ensg = symbol_to_ensg.get(interactor_symbol)
            if not interactor_ensg:
                continue
            interactor_uniprot = ensg_to_uniprot.get(interactor_ensg)
            if not interactor_uniprot or interactor_uniprot not in entity_to_id:
                continue
            interactor_idx = entity_to_id[interactor_uniprot]

            # Score protein -> interactor (PPI)
            with torch.no_grad():
                s2 = model.score_hrt(torch.tensor([[
                    protein_idx, ppi_id, interactor_idx]])).item()

            # Get diseases for interactor
            for disease_id, assoc_score in gene_disease_map.get(interactor_ensg, []):
                if (drug, disease_id) in known_pairs:
                    continue
                if disease_id not in entity_to_id:
                    continue
                disease_idx = entity_to_id[disease_id]

                # Score interactor -> disease
                with torch.no_grad():
                    s3 = model.score_hrt(torch.tensor([[
                        interactor_idx, assoc_id, disease_idx]])).item()

                combined = (s1 + s2 + s3) * assoc_score
                if disease_id not in disease_scores or combined > disease_scores[disease_id]:
                    disease_scores[disease_id] = combined

    # Top 3 per drug
    top = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for disease_id, score in top:
        name = disease_name_map.get(disease_id, '')
        if not name or name.startswith('obsolete'):
            continue
        all_predictions.append({
            'drug_id': drug,
            'drug_name': drug_name_map.get(drug, drug),
            'disease_id': disease_id,
            'disease_name': name,
            'score': score
        })

    if i % 300 == 0:
        print(f"  {i}/{len(drugs)}, predictions so far: {len(all_predictions)}")

print(f"\nTotal predictions: {len(all_predictions)}")

if len(all_predictions) == 0:
    print("No predictions generated.")
else:
    pred_df = pd.DataFrame(all_predictions)
    pred_df = pred_df.sort_values('score', ascending=False).reset_index(drop=True)
    min_s = pred_df['score'].min()
    max_s = pred_df['score'].max()
    pred_df['confidence'] = ((pred_df['score'] - min_s) / (max_s - min_s)).round(3)
    pred_df = pred_df.drop(columns=['score'])
    pred_df['confidence'] = ((pred_df['score'] - min_s) / (max_s - min_s)).round(3)
    pred_df = pred_df.drop(columns=['score'])  # ← after this line

# Filter out non-disease terms
    exclude_terms = ['count', 'measurement', 'ratio', 'percentage',
                 'level', 'volume', 'mass', 'system disease',
                 'disorder', 'finding', 'structure']
    pred_df = pred_df[~pred_df['disease_name'].str.lower().str.contains(
    '|'.join(exclude_terms), na=False)]
    pred_df = pred_df.reset_index(drop=True)

    print(f"\nTop 20 Novel Repurposing Predictions:")
    print("="*80)
    print(f"{'#':<4} {'Drug':<25} {'Disease':<35} {'Conf':>6}")
    print("-"*80)
    for i, row in pred_df.head(20).iterrows():
        print(f"{i+1:<4} {str(row['drug_name']):<25} {str(row['disease_name']):<35} {row['confidence']:>6.3f}")
    print("="*80)

    pred_df.to_csv("data/processed/novel_predictions.csv", index=False)
    print(f"Saved {len(pred_df)} predictions.")