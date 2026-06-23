import pandas as pd
from pykeen.triples import TriplesFactory

tf = TriplesFactory.from_path_binary("data/processed/splits/training")
entity_to_id = tf.entity_to_id

# What disease IDs actually exist in our KG?
disease_entities = [e for e in entity_to_id.keys() 
                   if e.startswith('EFO_') or e.startswith('MONDO_') 
                   or e.startswith('HP_') or e.startswith('Orphanet_')]

print(f"Total disease entities in KG: {len(disease_entities)}")
print("Sample:")
for d in disease_entities[:20]:
    print(f"  {d}")