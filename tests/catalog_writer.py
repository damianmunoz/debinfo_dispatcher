# dmd-module_translator/tests/catalog_writer.py
import csv
from typing import List, Dict

# Function to write the catalog edges to a CSV file
# Parameters:   
# - edges: List of edges where each edge is a dictionary with keys: source_type, source_id, target_type, target_id, relationship
# - output_file: Path to the output CSV file
def write_catalog(edges: List[Dict[str, str]], output_file: str):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["source_type", "source_id", "target_type", "target_id", "relationship"])
        writer.writeheader()
        writer.writerows(edges)