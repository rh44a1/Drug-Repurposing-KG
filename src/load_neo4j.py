from neo4j import GraphDatabase
import pandas as pd

URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "password123")

driver = GraphDatabase.driver(URI, auth=AUTH)

def run_query(query, params=None):
    with driver.session() as session:
        session.run(query, params or {})

# Create constraints first (speeds up loading massively)
print("Creating constraints...")
run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Drug) REQUIRE d.id IS UNIQUE")
run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protein) REQUIRE p.id IS UNIQUE")
run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (g:Gene) REQUIRE g.id IS UNIQUE")
run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (dis:Disease) REQUIRE dis.id IS UNIQUE")
print("Constraints created.")

# Load drug-target (ChEMBL)
print("Loading drug-target edges...")
drug_target = pd.read_csv("data/processed/drug_target.csv")
with driver.session() as session:
    for batch_start in range(0, len(drug_target), 1000):
        batch = drug_target.iloc[batch_start:batch_start+1000].to_dict('records')
        session.run("""
            UNWIND $rows AS row
            MERGE (d:Drug {id: row.drug_id})
              SET d.name = row.drug_name
            MERGE (p:Protein {id: row.uniprot_id})
              SET p.name = row.target_name
            MERGE (d)-[:TARGETS {weight: row.pchembl_value}]->(p)
        """, rows=batch)
        if batch_start % 10000 == 0:
            print(f"  {batch_start}/{len(drug_target)}")
print("Drug-target done.")

# Load gene-disease (Open Targets)
print("Loading gene-disease edges...")
gene_disease = pd.read_csv("data/processed/gene_disease.csv")
with driver.session() as session:
    for batch_start in range(0, len(gene_disease), 1000):
        batch = gene_disease.iloc[batch_start:batch_start+1000].to_dict('records')
        session.run("""
            UNWIND $rows AS row
            MERGE (g:Gene {id: row.targetId})
            MERGE (dis:Disease {id: row.diseaseId})
            MERGE (g)-[:ASSOCIATED_WITH {weight: row.associationScore}]->(dis)
        """, rows=batch)
print("Gene-disease done.")

# Load PPI (STRING) - sample 50k to keep Neo4j fast
print("Loading protein-protein edges (sampled)...")
ppi = pd.read_csv("data/processed/protein_protein.csv").sample(50000, random_state=42)
with driver.session() as session:
    for batch_start in range(0, len(ppi), 1000):
        batch = ppi.iloc[batch_start:batch_start+1000].to_dict('records')
        session.run("""
            UNWIND $rows AS row
            MERGE (p1:Protein {id: row.protein1})
              SET p1.gene_name = row.gene1
            MERGE (p2:Protein {id: row.protein2})
              SET p2.gene_name = row.gene2
            MERGE (p1)-[:INTERACTS_WITH {weight: row.combined_score}]->(p2)
        """, rows=batch)
        if batch_start % 10000 == 0:
            print(f"  {batch_start}/{len(ppi)}")
print("PPI done.")

print("\nAll done! Verifying...")
with driver.session() as session:
    result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
    for record in result:
        print(f"  {record['label']}: {record['count']} nodes")
    result = session.run("MATCH ()-[r]->() RETURN type(r) as rel, count(r) as count")
    for record in result:
        print(f"  {record['rel']}: {record['count']} edges")

driver.close()