import pandas as pd
import requests
import time
from pathlib import Path

string_map = pd.read_csv("esm_extension/string_to_uniprot.csv")
drug_target = pd.read_csv("data/processed/drug_target.csv")

uniprot_ids = set(string_map['uniprot_id'].dropna().tolist())
uniprot_ids.update(drug_target['uniprot_id'].dropna().tolist())
uniprot_ids = list(uniprot_ids)
print(f"Total unique UniProt IDs: {len(uniprot_ids)}")

def parse_fasta(text):
    sequences = {}
    current_id = None
    current_seq = []
    for line in text.strip().split('\n'):
        if not line:
            continue
        if line.startswith('>'):
            if current_id and current_seq:
                sequences[current_id] = ''.join(current_seq)
            parts = line.split('|')
            current_id = parts[1] if len(parts) > 1 else line[1:].split()[0]
            current_seq = []
        else:
            current_seq.append(line.strip())
    if current_id and current_seq:
        sequences[current_id] = ''.join(current_seq)
    return sequences

def fetch_sequences_batch(ids, batch_size=50):
    sequences = {}
    total_batches = (len(ids) + batch_size - 1) // batch_size
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        batch_num = i // batch_size + 1
        if batch_num % 20 == 0:
            print(f"Batch {batch_num}/{total_batches}, total so far: {len(sequences)}")
        
        # Use the dedicated batch endpoint
        r = requests.post(
            "https://rest.uniprot.org/uniprotkb/batch",
            data={"ids": ",".join(batch), "format": "fasta"}
        )
        if r.status_code == 200 and r.text.strip():
            batch_seqs = parse_fasta(r.text)
            sequences.update(batch_seqs)
        time.sleep(0.3)
    return sequences

sequences = fetch_sequences_batch(uniprot_ids)
print(f"\nTotal fetched: {len(sequences)} / {len(uniprot_ids)}")

with open("esm_extension/proteins.fasta", 'w') as f:
    for uid, seq in sequences.items():
        f.write(f">{uid}\n{seq}\n")

print("Saved to esm_extension/proteins.fasta")