# src/build_validation_script.py
import pandas as pd
import psycopg2

conn = psycopg2.connect(
    host="unmtid-dbs.net", port=5433,
    dbname="drugcentral", user="drugman", password="dosage"
)

query = """
SELECT
    s.name AS drug_name,
    s.inchikey,
    s.smiles,
    di.concept_name AS disease_name,
    di.umls_cui,
    di.snomed_conceptid,
    EXTRACT(YEAR FROM a.approval) AS approval_year,
    a.type AS approval_source
FROM omop_relationship di
JOIN structures s ON s.id = di.struct_id
JOIN approval a ON a.struct_id = di.struct_id
WHERE
    di.relationship_name = 'indication'
    AND a.approval IS NOT NULL
    AND a.type IN ('FDA', 'EMA')
ORDER BY a.approval;
"""

print("Querying indications...")
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()
cols = [desc[0] for desc in cur.description]
conn.close()

df = pd.DataFrame(rows, columns=cols)
df['approval_year'] = df['approval_year'].astype(int)

print(f"Total drug-indication pairs: {len(df)}")
print(f"Year range: {df['approval_year'].min()} - {df['approval_year'].max()}")
print(f"\nPairs per year (last 15 years):")
print(df['approval_year'].value_counts().sort_index().tail(15))

# Temporal split: train = before 2021, test = 2021 onwards
# (gives ~3 years of held-out approvals as test set)
train_df = df[df['approval_year'] < 2021]
test_df  = df[df['approval_year'] >= 2021]

print(f"\nTrain set (pre-2021): {len(train_df)} pairs")
print(f"Test set  (2021+):    {len(test_df)} pairs")
print(f"\nTest diseases sample:\n{test_df['disease_name'].value_counts().head(10)}")

df.to_csv("data/raw/drugcentral_indications.csv", index=False)
train_df.to_csv("data/processed/dc_train.csv", index=False)
test_df.to_csv("data/processed/dc_test.csv", index=False)
print("\nSaved all three files.")