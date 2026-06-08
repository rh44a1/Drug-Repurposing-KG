# Drug Repurposing via Biomedical Knowledge Graph Embedding

> **Preprint:** [BIORXIV/2026/730814](https://www.biorxiv.org/content/10.1101/2026.730814) — *Drug Repurposing via Biomedical Knowledge Graph Embedding: Ranking Loss Outperforms GNNs Despite Lower AUC*

This project builds a large-scale biomedical knowledge graph (KG) from four public databases, trains Knowledge Graph Embedding (KGE) and Graph Neural Network (GNN) models, and predicts novel drug–disease associations for drug repurposing.

**Key finding:** RotatE with ranking loss (MRR: 0.1995) substantially outperforms GNNs (MRR: 0.0069) despite GNNs achieving higher AUC (0.97), demonstrating that metric choice critically affects model selection for this task.

---

## Results Summary

| Model | Type | MRR | Hits@1 | Hits@10 | AUC |
|---|---|---|---|---|---|
| TransE | KGE | 0.0889 | 0.0230 | 0.2100 | — |
| **RotatE** | **KGE** | **0.1995** | **0.1160** | **0.3546** | — |
| ComplEx | KGE | 0.0217 | 0.0041 | 0.0525 | — |
| RotatE (weighted-sampling) | KGE | 0.0947 | 0.0366 | 0.2095 | — |
| RotatE (weighted-loss) | KGE | 0.1419 | 0.0683 | 0.2765 | — |
| GraphSAGE | GNN | 0.0069 | 0.0010 | 0.0170 | 0.9744 |
| GAT | GNN | 0.0002 | 0.0000 | 0.0000 | 0.7075 |

**Top validated prediction:** Palbociclib → Bladder Cancer (confirmed in active clinical trials)

---

## Knowledge Graph

Built from 4 public databases:

| Database | Relation | Triples |
|---|---|---|
| ChEMBL 37 | Drug–target | 29,948 |
| Open Targets v26.03 | Gene–disease | 2,789 |
| STRING v12 | Protein–protein | 473,860 |
| STITCH v5 | Chemical–protein | 466,669 |
| **Total** | | **973,266** |

- **189,233 nodes** — 6,824 drugs, 45,129 proteins/genes, 137,280 diseases/other
- **4 relation types**
- **2,367 novel repurposing predictions** generated after filtering

---

## Project Structure

```
drug-repurposing-kg/
├── data/
│   ├── raw/                  # source database files (not in repo — see below)
│   └── processed/            # output CSVs, predictions, paths, figure
│       ├── drug_target.csv
│       ├── gene_disease.csv
│       ├── triples.csv
│       ├── dc_train.csv
│       ├── dc_test.csv
│       ├── novel_predictions.csv
│       ├── mechanistic_paths.csv
│       ├── jaccard_baseline.csv
│       ├── evaluation_results.csv
│       └── network_visualization.png
├── src/
│   ├── parse_chembl.py         # parse ChEMBL drug–target interactions
│   ├── parse_string.py         # parse STRING PPI data
│   ├── parse_stitch.py         # parse STITCH chemical–protein data
│   ├── build_graph.py          # construct NetworkX KG from parsed data
│   ├── link_proteins.py        # map UniProt IDs to HGNC gene symbols
│   ├── load_neo4j.py           # load KG into Neo4j
│   ├── map_diseases.py         # map disease identifiers
│   ├── decode_diseases.py      # decode EFO disease terms
│   ├── train_kge.py            # train TransE / RotatE / ComplEx via PyKEEN
│   ├── baseline.py             # Jaccard similarity baseline
│   ├── evaluate_rotae.py       # evaluate RotatE on DrugCentral test set
│   ├── predict.py              # generate drug–disease predictions
│   ├── filter_predic.py        # filter predictions (remove known, low confidence)
│   ├── map_drugcentral_to_kg.py # map DrugCentral indications to KG entities
│   ├── mechan_path.py          # trace 3-hop mechanistic paths
│   ├── fetch_all_diseases.py   # fetch disease names from ontology APIs
│   └── visualise_network.py    # generate Figure 1 (mechanistic path network)
└── README.md
```

---

## Setup

### Requirements

- Python 3.10+
- Google Colab T4 GPU (for model training)
- Neo4j Desktop 2.1.3 (optional, for graph queries)

### Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install pandas numpy networkx matplotlib rapidfuzz pyarrow
pip install pykeen torch torch-geometric
pip install neo4j
```

### Raw data (not included in repo)

Download and place in `data/raw/`:

| File | Source | URL |
|---|---|---|
| `chembl_37.db` | ChEMBL | [chembl.ebi.ac.uk](https://chembl.ebi.ac.uk/downloads) |
| `9606.protein.links.v12.0.txt.gz` | STRING | [string-db.org](https://string-db.org/cgi/download) |
| `9606.protein_chemical.links.detailed.v5.0.tsv` | STITCH | [stitch.embl.de](http://stitch.embl.de/download) |
| `opentargets_part*.parquet` | Open Targets | [platform.opentargets.org](https://platform.opentargets.org/downloads) |
| `gene_names.tsv` | HGNC API | auto-fetched by `link_proteins.py` |
| `drugcentral_indications.csv` | DrugCentral | [drugcentral.org](https://drugcentral.org/download) |

---

## Reproducing Results

```bash
# 1. Parse all data sources
python src/parse_chembl.py
python src/parse_string.py
python src/parse_stitch.py

# 2. Build the knowledge graph
python src/link_proteins.py
python src/build_graph.py

# 3. Train KGE models (run on Colab T4 for speed)
python src/train_kge.py

# 4. Evaluate and generate predictions
python src/baseline.py
python src/evaluate_rotae.py
python src/predict.py
python src/filter_predic.py

# 5. Trace mechanistic paths and visualise
python src/mechan_path.py
python src/visualise_network.py
```

---

## Top Repurposing Predictions

| Drug | Disease | Confidence | Mechanistic Path | Evidence |
|---|---|---|---|---|
| **Palbociclib** | Bladder cancer | 0.934 | CDK2 → HIF1A → Bladder cancer | Active clinical trials ✓ |
| Entrectinib | Alzheimer disease | 0.985 | CSF1R → TLR4 → Alzheimer | TRK/CSF1R neurodegeneration lit. |
| Sorafenib | Alzheimer disease | 0.958 | RAF/MEK → tau phosphorylation | Nature Sci Rep repurposing study |
| Ruxolitinib | Alzheimer disease | 0.952 | GAK → LRRK2 → Alzheimer | Published AD candidate (2023) |
| Vandetanib | Multiple sclerosis | 0.935 | VEGFR → angiogenesis → MS | Angiogenesis in MS lesion formation |
| Fostamatinib | Multiple sclerosis | 0.927 | FLT3 → ITGAM → MS | SYK/B-cell autoimmune mechanism |
| TG100-115 | Parkinson disease | 0.917 | EGFR → CTNNB1 → Parkinson | PI3K-γ neuroinflammation |

---

## Citation

If you use this code or data, please cite:

```bibtex
@article{sankar2026drugrepurposing,
  title   = {Drug Repurposing via Biomedical Knowledge Graph Embedding:
             Ranking Loss Outperforms GNNs Despite Lower AUC},
  author  = {Sankar, Rhea},
  journal = {bioRxiv},
  year    = {2026},
  doi     = {10.1101/2026.730814}
}
```

---

## Author

**Rhea Sankar** — github.com/rh44a1
