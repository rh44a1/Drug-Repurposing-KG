import pandas as pd

pred_df = pd.read_csv("data/processed/novel_predictions.csv")
print(f"Before filter: {len(pred_df)}")

exclude_terms = ['count', 'measurement', 'ratio', 'percentage',
                 'level', 'volume', 'mass', 'system disease',
                 'disorder', 'finding', 'structure', 'obsolete',
                 'total lipids', 'cholesterol', 'HDL', 'LDL', 'VLDL',
                 'response to', 'exposure', 'phenotype', 'trait', 'platelet', 'leukocyte', 'erythrocyte', 'lymphocyte', 
'neutrophil', 'monocyte', 'eosinophil', 'basophil',
'abnormality of', 'quantity']

pred_df = pred_df[~pred_df['disease_name'].str.lower().str.contains(
    '|'.join(exclude_terms), na=False, regex=True)]

pred_df = pred_df.reset_index(drop=True)
print(f"After filter: {len(pred_df)}")

print(f"\nTop 20 Novel Repurposing Predictions:")
print("="*80)
print(f"{'#':<4} {'Drug':<25} {'Disease':<35} {'Conf':>6}")
print("-"*80)
for i, row in pred_df.head(20).iterrows():
    print(f"{i+1:<4} {str(row['drug_name']):<25} {str(row['disease_name']):<35} {row['confidence']:>6.3f}")
print("="*80)

pred_df.to_csv("data/processed/novel_predictions.csv", index=False)
print(f"\nSaved {len(pred_df)} predictions.")