from neo4j import GraphDatabase
import pandas as pd
import ast

URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "password123")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Load HGNC mapping
hgnc = pd.read_csv("data/raw/gene_names.tsv", sep='\t')
hgnc = hgnc[hgnc['ensembl_gene_id'].notna() & hgnc['uniprot_ids'].notna()]

# Parse uniprot_ids from string list to first uniprot ID
def extract_uniprot(val):
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[0]
    except:
        return None
    return None

hgnc['uniprot_id'] = hgnc['uniprot_ids'].apply(extract_uniprot)
hgnc = hgnc[hgnc['uniprot_id'].notna()]

# ENSG -> UniProt mapping
ensg_to_uniprot = dict(zip(hgnc['ensembl_gene_id'], hgnc['uniprot_id']))
ensg_to_symbol = dict(zip(hgnc['ensembl_gene_id'], hgnc['symbol']))
print(f"Mapping size: {len(ensg_to_uniprot)}")

# Add SAME_AS edges between UniProt Protein nodes and ENSP Protein nodes
# via shared gene symbol from STRING info file
string_info = pd.read_csv("data/raw/9606.protein.info.v12.0.txt", sep='\t')
string_info = string_info.rename(columns={'#string_protein_id': 'string_id'})

# gene_symbol -> ENSP mapping from STRING
symbol_to_ensp = dict(zip(string_info['preferred_name'], string_info['string_id']))

# Build bridge: UniProt -> ENSP via gene symbol
bridges = []
for ensg, uniprot in ensg_to_uniprot.items():
    symbol = ensg_to_symbol.get(ensg)
    if symbol and symbol in symbol_to_ensp:
        ensp = symbol_to_ensp[symbol]
        bridges.append({'uniprot': uniprot, 'ensp': ensp, 'symbol': symbol})

bridges_df = pd.DataFrame(bridges)
print(f"Bridges found: {len(bridges_df)}")
print(bridges_df.head())

# Load bridges into Neo4j as SAME_PROTEIN edges
print("Loading bridges into Neo4j...")
with driver.session() as session:
    for batch_start in range(0, len(bridges_df), 1000):
        batch = bridges_df.iloc[batch_start:batch_start+1000].to_dict('records')
        session.run("""
            UNWIND $rows AS row
            MATCH (p1:Protein {id: row.uniprot})
            MATCH (p2:Protein {id: row.ensp})
            MERGE (p1)-[:SAME_PROTEIN {symbol: row.symbol}]->(p2)
        """, rows=batch)
        if batch_start % 5000 == 0:
            print(f"  {batch_start}/{len(bridges_df)}")

print("Done. Now testing full path query...")
with driver.session() as session:
    result = session.run("""
        MATCH (d:Drug)-[:TARGETS]->(p1:Protein)-[:SAME_PROTEIN]->(p2:Protein)-[:INTERACTS_WITH]->(p3:Protein)
        WHERE d.name = 'CETIRIZINE'
        RETURN d.name, p1.name, p2.id, p3.gene_name LIMIT 10
    """)
    for r in result:
        print(r)

driver.close()