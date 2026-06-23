import torch
import pickle
import pandas as pd
import numpy as np
from pykeen.triples import TriplesFactory

# Load trained model
print("Loading model...")
model = torch.load("models/rotate_esm2/trained_model.pkl", 
                   map_location='cpu', weights_only=False)
model.eval()

training = TriplesFactory.from_path_binary("data/processed/splits/training")
entity_to_id = training.entity_to_id
id_to_entity = {v: k for k, v in entity_to_id.items()}
relation_to_id = training.relation_to_id

drug_target = pd.read_csv("data/processed/drug_target.csv")
novel_preds = pd.read_csv("data/processed/novel_predictions.csv")
string_map = pd.read_csv("esm_extension/string_to_uniprot.csv")

# All proteins in KG
all_proteins = set(drug_target['uniprot_id'].dropna().tolist())
all_proteins.update(string_map['uniprot_id'].dropna().tolist())
protein_ids_in_kg = [p for p in all_proteins if p in entity_to_id]
print(f"Proteins in KG: {len(protein_ids_in_kg)}")

# Protein tensor for scoring
protein_indices = torch.tensor([entity_to_id[p] for p in protein_ids_in_kg])
targets_relation_id = relation_to_id['TARGETS']

# Known drug-protein pairs (to exclude already known)
known_pairs = set(zip(drug_target['drug_id'], drug_target['uniprot_id']))

# UniProt -> gene name map
uniprot_to_gene = dict(zip(drug_target['uniprot_id'], drug_target['target_name']))

def predict_drug_targets(drug_id, topk=10):
    if drug_id not in entity_to_id:
        return []
    
    drug_idx = entity_to_id[drug_id]
    rel_idx = targets_relation_id
    
    # Score all drug -> TARGETS -> protein triples
    drug_tensor = torch.tensor([drug_idx]).repeat(len(protein_ids_in_kg))
    rel_tensor = torch.tensor([rel_idx]).repeat(len(protein_ids_in_kg))
    
    with torch.no_grad():
        scores = model.score_hrt(
            torch.stack([drug_tensor, rel_tensor, protein_indices], dim=1)
        ).squeeze().numpy()
    
    # Rank and filter known
    ranked = sorted(zip(protein_ids_in_kg, scores), key=lambda x: -x[1])
    results = []
    for protein, score in ranked:
        if (drug_id, protein) not in known_pairs:
            gene = uniprot_to_gene.get(protein, protein)
            results.append((protein, gene, float(score)))
        if len(results) >= topk:
            break
    return results

# Run for top 10 repurposing candidates
top_drugs = novel_preds.head(10)
all_results = []

print("\n=== Drug → Protein Binding Predictions ===\n")
for _, row in top_drugs.iterrows():
    drug_id = row['drug_id']
    drug_name = row['drug_name']
    disease = row['disease_name']
    confidence = row['confidence']
    
    targets = predict_drug_targets(drug_id, topk=5)
    print(f"{drug_name} → {disease} (repurposing confidence: {confidence:.3f})")
    for protein, gene, score in targets:
        print(f"    → {gene} ({protein})  binding score: {score:.4f}")
    print()
    
    for protein, gene, score in targets:
        all_results.append({
            'drug_id': drug_id,
            'drug_name': drug_name,
            'disease_name': disease,
            'repurposing_confidence': confidence,
            'predicted_target_uniprot': protein,
            'predicted_target_gene': gene,
            'binding_score': score
        })

# Save
out = pd.DataFrame(all_results)
out.to_csv("esm_extension/drug_protein_predictions.csv", index=False)
print("Saved to esm_extension/drug_protein_predictions.csv")