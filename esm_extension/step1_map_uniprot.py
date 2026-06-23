import gzip
import pandas as pd
from pathlib import Path

print("Parsing STRING alias file...")

mapping = {}
with gzip.open("data/raw/9606.protein.aliases.v12.0.txt.gz", 'rt', encoding='utf-8') as f:
    next(f)  # skip header
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) != 3:
            continue
        string_id, alias, source = parts
        if 'UniProt_AC' in source or 'UniProt_SWISS' in source:
            if string_id not in mapping:  # take first hit
                mapping[string_id] = alias

print(f"Mapped: {len(mapping)} proteins")

# Check coverage against your actual proteins
df = pd.read_csv("data/processed/protein_protein.csv")
unique_proteins = pd.concat([df['protein1'], df['protein2']]).unique()
covered = [p for p in unique_proteins if p in mapping]
print(f"Coverage: {len(covered)} / {len(unique_proteins)}")

# Save
out = pd.DataFrame(list(mapping.items()), columns=["string_id", "uniprot_id"])
Path("esm_extension").mkdir(exist_ok=True)
out.to_csv("esm_extension/string_to_uniprot.csv", index=False)
print("Saved to esm_extension/string_to_uniprot.csv")