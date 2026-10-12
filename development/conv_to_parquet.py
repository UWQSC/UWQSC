import pandas as pd

df = pd.read_csv('data/hackathon_sample_v2.csv')
df.to_parquet('data/hackathon_sample_v2.parquet', engine='pyarrow', index=False)

print("Conversion complete! Now use the Parquet file in Streamlit.")