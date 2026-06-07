from neo4j import GraphDatabase
import pandas as pd

URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "password123")
driver = GraphDatabase.driver(URI, auth=AUTH)

queries = {
    "RUXOLITINIB → Alzheimer": {
        "drug": "RUXOLITINIB",
        "disease_id": "MONDO_0004975"
    },
    "ENTRECTINIB → Alzheimer": {
        "drug": "ENTRECTINIB", 
        "disease_id": "MONDO_0004975"
    },
    "FOSTAMATINIB → Multiple Sclerosis": {
        "drug": "FOSTAMATINIB",
        "disease_id": "EFO_0003885"
    },
    "PALBOCICLIB → Bladder Cancer": {
        "drug": "PALBOCICLIB",
        "disease_id": "EFO_0000292"
    },
    "TG100-115 → Parkinson": {
        "drug": "TG100-115",
        "disease_id": "MONDO_0005180"
    }
}

results = []

with driver.session() as session:
    for prediction_name, params in queries.items():
        print(f"\n{'='*60}")
        print(f"Prediction: {prediction_name}")
        print(f"{'='*60}")

        # Find mechanistic paths
        result = session.run("""
            MATCH (d:Drug)-[:TARGETS]->(p1:Protein)-[:SAME_PROTEIN]->(p2:Protein)
                  -[:INTERACTS_WITH]->(p3:Protein)
            WHERE d.name = $drug
            RETURN d.name AS drug,
                   p1.name AS direct_target,
                   p2.gene_name AS target_gene,
                   p3.gene_name AS interactor
            LIMIT 10
        """, drug=params["drug"])

        paths = result.data()
        if not paths:
            print("  No paths found in Neo4j")
            continue

        print(f"  Drug: {params['drug']}")
        print(f"  Mechanistic paths:")
        for path in paths:
            print(f"    {path['drug']} → targets → {path['direct_target']} "
                  f"({path['target_gene']}) → interacts with → {path['interactor']}")
            results.append({
                'prediction': prediction_name,
                'drug': path['drug'],
                'direct_target': path['direct_target'],
                'target_gene': path['target_gene'],
                'interactor': path['interactor']
            })

driver.close()

# Save
results_df = pd.DataFrame(results)
results_df.to_csv("data/processed/mechanistic_paths.csv", index=False)
print(f"\nSaved to data/processed/mechanistic_paths.csv")
print(results_df)