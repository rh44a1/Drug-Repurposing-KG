import torch
import pandas as pd
import numpy as np
from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline
from pykeen.nn.init import PretrainedInitializer
import os

print("Loading splits...")
training = TriplesFactory.from_path_binary("data/processed/splits/training")
validation = TriplesFactory.from_path_binary("data/processed/splits/validation")
testing = TriplesFactory.from_path_binary("data/processed/splits/testing")
print(f"Train: {training.num_triples}, Val: {validation.num_triples}, Test: {testing.num_triples}")

# Load ESM2 embeddings
print("Loading ESM2 embeddings...")
esm2_embeddings = torch.load("esm_extension/protein_esm2_embeddings.pt", 
                              map_location='cpu', weights_only=False)

# Build entity initializer tensor
# PyKEEN entity order comes from training.entity_to_id
entity_to_id = training.entity_to_id
num_entities = training.num_entities
EMBEDDING_DIM = 128  # must match model embedding_dim

# Project ESM2 (1280-dim) -> 128-dim with a linear layer
projection = torch.nn.Linear(1280, EMBEDDING_DIM)
torch.nn.init.xavier_uniform_(projection.weight)

# Build init tensor: random for non-protein nodes, projected ESM2 for proteins
init_tensor = torch.zeros(num_entities, EMBEDDING_DIM)
esm2_count = 0

with torch.no_grad():
    for entity, idx in entity_to_id.items():
        if entity in esm2_embeddings:
            projected = projection(esm2_embeddings[entity].unsqueeze(0)).squeeze(0)
            init_tensor[idx] = projected
            esm2_count += 1
        else:
            # random init for drugs, diseases, pathways
            init_tensor[idx] = torch.nn.init.xavier_uniform_(
                torch.empty(1, EMBEDDING_DIM)
            ).squeeze(0)

print(f"Entities initialized with ESM2: {esm2_count} / {num_entities}")

# Train RotatE with ESM2-initialized protein embeddings
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Training on: {device}")

result = pipeline(
    training=training,
    validation=validation,
    testing=testing,
    model='TransE',  # change from RotatE
    model_kwargs=dict(
        embedding_dim=EMBEDDING_DIM,
        entity_initializer=PretrainedInitializer(tensor=init_tensor),
    ),
    optimizer='Adam',
    optimizer_kwargs=dict(lr=0.001),
    training_kwargs=dict(num_epochs=50, batch_size=1024),
    evaluation_kwargs=dict(batch_size=16),
    random_seed=42,
    device=device,
)
os.makedirs("models/transe_esm2", exist_ok=True)
result.save_to_directory("models/transe_esm2")

metrics = result.metric_results.to_flat_dict()
print(f"\nRotatE + ESM2 Results:")
print(f"  MRR:     {metrics.get('both.realistic.inverse_harmonic_mean_rank', 'N/A'):.4f}")
print(f"  Hits@1:  {metrics.get('both.realistic.hits_at_1', 'N/A'):.4f}")
print(f"  Hits@10: {metrics.get('both.realistic.hits_at_10', 'N/A'):.4f}")