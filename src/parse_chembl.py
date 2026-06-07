import sqlite3
import pandas as pd
import os

conn = sqlite3.connect("data/raw/chembl_37.db")

query = """
SELECT
    md.chembl_id AS drug_id,
    md.pref_name AS drug_name,
    td.chembl_id AS target_id,
    td.pref_name AS target_name,
    cs.accession AS uniprot_id,
    act.pchembl_value
FROM activities act
JOIN assays ass ON act.assay_id = ass.assay_id
JOIN target_dictionary td ON ass.tid = td.tid
JOIN molecule_dictionary md ON act.molregno = md.molregno
JOIN target_components tc ON td.tid = tc.tid
JOIN component_sequences cs ON tc.component_id = cs.component_id
WHERE td.target_type = 'SINGLE PROTEIN'
AND act.standard_type IN ('IC50', 'Ki', 'Kd', 'EC50')
AND act.pchembl_value IS NOT NULL
AND act.pchembl_value >= 6.0
"""

print("Querying ChEMBL...")
df = pd.read_sql(query, conn)

df_dedup = df.groupby(['drug_id', 'target_id', 'uniprot_id'], as_index=False).agg(
    drug_name=('drug_name', 'first'),
    target_name=('target_name', 'first'),
    pchembl_value=('pchembl_value', 'max')
)

df_final = df_dedup[df_dedup['drug_name'].notna()]

print(f"Final shape: {df_final.shape}")
print(f"Unique drugs: {df_final['drug_id'].nunique()}")
print(f"Unique targets: {df_final['target_id'].nunique()}")
print(df_final.head())

os.makedirs("data/processed", exist_ok=True)
df_final.to_csv("data/processed/drug_target.csv", index=False)
print("Saved to data/processed/drug_target.csv")