import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import ast

# Load data
drug_target = pd.read_csv("data/processed/drug_target.csv")
hgnc = pd.read_csv("data/raw/gene_names.tsv", sep='\t')

def extract_uniprot(val):
    try:
        parsed = ast.literal_eval(val)
        return parsed[0] if parsed else None
    except:
        return None

hgnc = hgnc[hgnc['ensembl_gene_id'].notna() & hgnc['uniprot_ids'].notna()]
hgnc['uniprot_id'] = hgnc['uniprot_ids'].apply(extract_uniprot)
uniprot_to_symbol = dict(zip(hgnc['uniprot_id'], hgnc['symbol']))
manual_symbols = {'Q78DX7': 'NTRK2'}
uniprot_to_symbol.update(manual_symbols)

drug = 'ENTRECTINIB'
drug_id = 'CHEMBL2403108'
disease = 'Alzheimer\ndisease'

targets = drug_target[drug_target['drug_id'] == drug_id][['uniprot_id', 'target_name']].values.tolist()

G = nx.DiGraph()
G.add_node(drug, node_type='drug')

target_symbols = []
for uniprot, target_name in targets[:6]:
    symbol = uniprot_to_symbol.get(uniprot, uniprot)
    target_symbols.append(symbol)
    G.add_node(symbol, node_type='protein')
    G.add_edge(drug, symbol, edge_type='TARGETS')

interactors = ['TLR4', 'PIK3R1', 'SHC1', 'CD4', 'CSF2']
for interactor in interactors:
    G.add_node(interactor, node_type='interactor')
    G.add_edge('CSF1R', interactor, edge_type='INTERACTS_WITH')

G.add_node(disease, node_type='disease')
G.add_edge('TLR4', disease, edge_type='ASSOCIATED_WITH')
G.add_edge('PIK3R1', disease, edge_type='ASSOCIATED_WITH')

# Positions
pos = {}
pos[drug] = (0, 3)

target_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'protein']
for i, t in enumerate(target_nodes):
    pos[t] = (3, i * 1.1)

interactor_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'interactor']
for i, n in enumerate(interactor_nodes):
    pos[n] = (6, i * 1.1)

pos[disease] = (9, 2.2)

for n in G.nodes():
    if n not in pos:
        pos[n] = (4.5, 3)

# Academic style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.titlesize': 13,
})

fig, ax = plt.subplots(figsize=(16, 10))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Node colors — academic palette
color_map = {
    'drug':       '#2166AC',
    'protein':    '#F4A582',
    'interactor': '#92C5DE',
    'disease':    '#D6604D'
}
node_colors = [color_map.get(G.nodes[n].get('node_type'), '#CCCCCC') for n in G.nodes()]

node_sizes = []
for n in G.nodes():
    t = G.nodes[n].get('node_type')
    if t == 'drug': node_sizes.append(4000)
    elif t == 'disease': node_sizes.append(4000)
    else: node_sizes.append(2200)

# Edge colors
edge_colors = []
edge_widths = []
edge_styles = []
for u, v, d in G.edges(data=True):
    if d.get('edge_type') == 'TARGETS':
        edge_colors.append('#2166AC')
        edge_widths.append(2.0)
        edge_styles.append('solid')
    elif d.get('edge_type') == 'INTERACTS_WITH':
        edge_colors.append('#4DAC26')
        edge_widths.append(1.8)
        edge_styles.append('solid')
    else:
        edge_colors.append('#D6604D')
        edge_widths.append(2.5)
        edge_styles.append('dashed')

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                       alpha=1.0, ax=ax, linewidths=1.5,
                       edgecolors='#333333')

# Draw labels
nx.draw_networkx_labels(G, pos, font_size=9, font_color='#111111',
                        font_family='serif', font_weight='bold', ax=ax)

# Draw edges separately by type for style control
for (u, v, d), color, width in zip(G.edges(data=True), edge_colors, edge_widths):
    style = 'dashed' if d.get('edge_type') == 'ASSOCIATED_WITH' else 'solid'
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)],
                           edge_color=color, width=width,
                           style=style,
                           arrows=True, arrowsize=18,
                           ax=ax,
                           connectionstyle='arc3,rad=0.08',
                           min_source_margin=25,
                           min_target_margin=25)

# Edge labels
edge_labels = {(u, v): d['edge_type'].replace('_', ' ').title()
               for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                              font_size=7, font_family='serif',
                              font_color='#444444', ax=ax,
                              bbox=dict(boxstyle='round,pad=0.2',
                                       facecolor='white', alpha=0.7,
                                       edgecolor='none'))

# Legend
legend_elements = [
    mpatches.Patch(facecolor='#2166AC', edgecolor='#333', label='Drug (Entrectinib)'),
    mpatches.Patch(facecolor='#F4A582', edgecolor='#333', label='Direct Target'),
    mpatches.Patch(facecolor='#92C5DE', edgecolor='#333', label='Interacting Protein'),
    mpatches.Patch(facecolor='#D6604D', edgecolor='#333', label='Disease'),
    plt.Line2D([0], [0], color='#2166AC', linewidth=2, label='Targets'),
    plt.Line2D([0], [0], color='#4DAC26', linewidth=2, label='Interacts With'),
    plt.Line2D([0], [0], color='#D6604D', linewidth=2,
               linestyle='dashed', label='Associated With'),
]
legend = ax.legend(handles=legend_elements, loc='upper left',
                   frameon=True, fancybox=False,
                   edgecolor='#AAAAAA', fontsize=9,
                   prop={'family': 'serif'})

# Title and annotations
ax.set_title('Figure 1. Mechanistic Pathway: Entrectinib → Alzheimer Disease\n'
             'Drug–protein–disease path via CSF1R–TLR4 neuroinflammation axis',
             fontsize=12, fontfamily='serif', fontweight='bold',
             loc='center', pad=15, color='#111111')

# Column headers
ax.text(0, 6.5, 'Drug', ha='center', fontsize=10, fontfamily='serif',
        color='#2166AC', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF3FB', edgecolor='#2166AC'))
ax.text(3, 6.5, 'Direct Targets', ha='center', fontsize=10, fontfamily='serif',
        color='#8B4513', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEF0E6', edgecolor='#F4A582'))
ax.text(6, 6.5, 'Interacting Proteins', ha='center', fontsize=10, fontfamily='serif',
        color='#1A5276', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#EBF5FB', edgecolor='#92C5DE'))
ax.text(9, 6.5, 'Disease', ha='center', fontsize=10, fontfamily='serif',
        color='#922B21', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC', edgecolor='#D6604D'))

ax.set_xlim(-1.5, 11)
ax.set_ylim(-1, 7.5)
ax.axis('off')

# Border
for spine in ax.spines.values():
    spine.set_visible(False)

rect = plt.Rectangle((0, 0), 1, 1, fill=False, edgecolor='#CCCCCC',
                      linewidth=1, transform=ax.transAxes)
ax.add_patch(rect)

plt.tight_layout()
plt.savefig('data/processed/network_visualization.png', dpi=300,
            bbox_inches='tight', facecolor='white')
plt.show()
print("Saved.")