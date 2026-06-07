import pandas as pd
from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline
import torch
import os

# Load splits
print("Loading splits...")
training = TriplesFactory.from_path_binary("data/processed/splits/training")
validation = TriplesFactory.from_path_binary("data/processed/splits/validation")
testing = TriplesFactory.from_path_binary("data/processed/splits/testing")
print(f"Train: {training.num_triples}, Val: {validation.num_triples}, Test: {testing.num_triples}")

# Check GPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Training on: {device}")

# Train TransE
print("\nTraining TransE...")
result = pipeline(
    training=training,
    validation=validation,
    testing=testing,
    model='TransE',
    model_kwargs=dict(embedding_dim=128),
    optimizer='Adam',
    optimizer_kwargs=dict(lr=0.001),
    training_kwargs=dict(num_epochs=50, batch_size=1024),
    evaluation_kwargs=dict(batch_size=16),
    random_seed=42,
    device=device,
)

# Save results
os.makedirs("models/transe", exist_ok=True)
result.save_to_directory("models/transe")
print("\nTransE saved to models/transe/")

# Print metrics
metrics = result.metric_results.to_flat_dict()
print(f"\nTransE Results:")
print(f"  MRR:     {metrics.get('both.realistic.inverse_harmonic_mean_rank', 'N/A'):.4f}")
print(f"  Hits@1:  {metrics.get('both.realistic.hits_at_1', 'N/A'):.4f}")
print(f"  Hits@10: {metrics.get('both.realistic.hits_at_10', 'N/A'):.4f}")