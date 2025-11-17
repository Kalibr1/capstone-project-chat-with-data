import pandas as pd
from datasets import load_dataset
import sqlite3

# Define the dataset repository and the specific file
dataset_name = "Pablinho/movies-dataset"
data_file = "9000plus.csv"

print(f"Loading {data_file} from {dataset_name}...")

# 1. Load the dataset from Hugging Face
# We use the 'data_files' argument to load only the specific file
ds = load_dataset(dataset_name, data_files=data_file)

# 2. Convert the dataset (which is in the 'train' split by default) to pandas
# load_dataset returns a DatasetDict; 'train' is the default key
df = ds['train'].to_pandas()

# 3. Display the results
print("\nSuccessfully loaded dataset!")
print(f"Total rows: {len(df)}")
print("\nDataFrame Head:")
print(df.head())

print("\nDataFrame Info:")
df.info()


# 4. Save the DataFrame to a local SQLite database
db_filename = "movies.db"
table_name = "movies"

# Create a connection
conn = sqlite3.connect(db_filename)

# Save the DataFrame to the SQL database
# if_exists='replace' will overwrite the table if it already exists
df.to_sql(table_name, conn, if_exists="replace", index=False)

# Close the connection
conn.close()

print(f"\nData saved to {db_filename} in table '{table_name}'")