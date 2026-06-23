import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from rich import box
from rich.text import Text
from rich.rule import Rule

console = Console()

# Load data
predictions = pd.read_csv("esm_extension/drug_protein_predictions.csv")
paths = pd.read_csv("esm_extension/mechanistic_paths.csv")
novel_preds = pd.read_csv("data/processed/novel_predictions.csv")

# ── Header ──────────────────────────────────────────────────────────────────
console.print()
console.rule("[bold purple]ESM2-Enhanced Drug Repurposing Pipeline[/bold purple]")
console.print()

# ── Model comparison ─────────────────────────────────────────────────────────
console.print(Panel("[bold]Model Performance Comparison[/bold]", style="purple"))
table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
table.add_column("Model", style="white", width=25)
table.add_column("MRR", justify="center", width=10)
table.add_column("Hits@1", justify="center", width=10)
table.add_column("Hits@10", justify="center", width=10)
table.add_column("Improvement", justify="center", width=15)

table.add_row("RotatE (baseline)", "0.2000", "—", "—", "—", style="dim")
table.add_row("TransE + ESM2", "0.0843", "0.0227", "0.1974", "[red]↓ worse[/red]")
table.add_row("RotatE + ESM2", "[bold green]0.3976[/bold green]", "[bold green]0.2536[/bold green]", "[bold green]0.6600[/bold green]", "[bold green]↑ +98.8% MRR[/bold green]")

console.print(table)
console.print()

# ── Pipeline flow ─────────────────────────────────────────────────────────────
console.print(Panel("[bold]Pipeline Architecture[/bold]", style="purple"))
console.print()

steps = [
    ("1", "STRING + UniProt", "16,201 proteins → 16,000 mapped (98.8%)", "cyan"),
    ("2", "Sequence Fetch", "7,884 protein sequences from UniProt FASTA", "cyan"),
    ("3", "ESM2-650M Embeddings", "7,884 × 1,280-dim vectors (Colab T4 GPU)", "green"),
    ("4", "Projection + KGE Init", "1,280 → 128 dim | 3,267 protein nodes enriched", "green"),
    ("5", "RotatE Retraining", "973K triples | 100 epochs | MRR 0.20 → 0.40", "yellow"),
    ("6", "Drug→Protein Prediction", "Novel binding targets for top repurposing hits", "magenta"),
    ("7", "Mechanistic Paths", "Drug → Protein → Gene → Disease", "magenta"),
]

for i, (num, title, detail, color) in enumerate(steps):
    console.print(f"  [bold {color}][ {num} ][/bold {color}]  [bold white]{title}[/bold white]")
    console.print(f"        [dim]{detail}[/dim]")
    if i < len(steps) - 1:
        console.print(f"         [dim]│[/dim]")
        console.print(f"         [dim]▼[/dim]")
console.print()

# ── Drug → Protein predictions ────────────────────────────────────────────────
console.print(Panel("[bold]Drug → Protein Binding Predictions[/bold]", style="purple"))
console.print()

top_drugs = predictions['drug_name'].unique()[:5]

for drug in top_drugs:
    drug_data = predictions[predictions['drug_name'] == drug].iloc[0]
    disease = drug_data['disease_name']
    rep_conf = drug_data['repurposing_confidence']

    tree = Tree(
        f"[bold yellow]💊 {drug}[/bold yellow]  [dim]→ repurposed for[/dim]  [bold cyan]{disease}[/bold cyan]  [dim](confidence: {rep_conf:.3f})[/dim]"
    )

    targets = predictions[predictions['drug_name'] == drug].head(5)
    for _, row in targets.iterrows():
        score = row['binding_score']
        gene = row['predicted_target_gene'][:45]
        protein = row['predicted_target_uniprot']
        branch = tree.add(
            f"[green]⬡ {gene}[/green]  [dim]({protein})[/dim]  [dim]score: {score:.4f}[/dim]"
        )

    console.print(tree)
    console.print()

# ── Mechanistic paths ─────────────────────────────────────────────────────────
console.print(Panel("[bold]Mechanistic Paths: Drug → Protein → Disease[/bold]", style="purple"))
console.print()

for _, row in paths.iterrows():
    drug = row['drug_name']
    gene = row['predicted_target_gene']
    protein = row['predicted_target_uniprot']
    ensg = row['ensembl_id']
    mech_disease = row['mechanistic_disease']
    rep_disease = row['repurposing_disease']
    score = row['binding_score']

    console.print(f"  [bold yellow]{drug}[/bold yellow]")
    console.print(f"    [dim]Repurposing target:[/dim] [cyan]{rep_disease}[/cyan]")
    console.print()
    console.print(
        f"    [yellow]{drug}[/yellow]"
        f" [dim]──TARGETS──▶[/dim] "
        f"[green]{gene}[/green] [dim]({protein})[/dim]"
        f" [dim]──EXPRESSED──▶[/dim] "
        f"[blue]{ensg}[/blue]"
        f" [dim]──ASSOCIATED──▶[/dim] "
        f"[magenta]{mech_disease[:40]}[/magenta]"
    )
    console.print(f"    [dim]Binding score: {score:.4f}[/dim]")
    console.print()

# ── Summary ───────────────────────────────────────────────────────────────────
console.rule("[bold purple]Summary[/bold purple]")
console.print()

summary = Table(box=box.SIMPLE, show_header=False)
summary.add_column(width=35)
summary.add_column(width=20)
summary.add_row("[dim]Unique drugs analyzed[/dim]", f"[bold]{predictions['drug_name'].nunique()}[/bold]")
summary.add_row("[dim]Novel protein targets predicted[/dim]", f"[bold]{predictions['predicted_target_uniprot'].nunique()}[/bold]")
summary.add_row("[dim]Mechanistic paths found[/dim]", f"[bold]{len(paths)}[/bold]")
summary.add_row("[dim]KG nodes[/dim]", "[bold]189,233[/bold]")
summary.add_row("[dim]KG triples[/dim]", "[bold]973,266[/bold]")
summary.add_row("[dim]Proteins with ESM2 embeddings[/dim]", "[bold]3,267[/bold]")

console.print(summary)
console.print()