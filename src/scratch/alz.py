import pandas as pd

disease_names = pd.read_csv("data/processed/disease_names.csv")
alz = disease_names[disease_names['disease_name'].str.lower().str.contains('alzheimer')]
print(alz)