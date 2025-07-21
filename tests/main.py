# dmd-module_translator/tests/main.py
import os
from sbom_loader import detect_format, load_sbom
from astra_parser import parse_spdx, parse_cyclonedx
from catalog_writer import write_catalog

def process_sbom_file(file_path: str, output_dir: str):
    fmt = detect_format(file_path)
    sbom = load_sbom(file_path)
    if fmt == 'spdx':
        edges = parse_spdx(sbom)
    elif fmt == 'cyclonedx':
        edges = parse_cyclonedx(sbom)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    base = os.path.basename(file_path).replace('.json', '').replace('.spdx', '') # Remove file extension from the base name
    output_file = os.path.join(output_dir, f'{base}_astra.csv') # Define the output file name
    write_catalog(edges, output_file) # Write the edges to a CSV file

if __name__ == '__main__':
    sbom_root = '../../sbom_data/bom-shelter/in-the-wild/cyclonedx' # Directory containing SBOM files
    if not os.path.exists(sbom_root): # Check if the directory exists
        raise FileNotFoundError(f"SBOM directory not found: {sbom_root}")
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True) # Ensure the output directory exists
    for root, _, files in os.walk(sbom_root): # Traverse the directory tree
        for file in files: # Check each file in the directory
            if file.endswith('.json') or file.endswith('.spdx'): # Check for JSON or SPDX files
                full_path = os.path.join(root, file)
                try:
                    process_sbom_file(full_path, output_dir) # Process the SBOM file
                except Exception as e:
                    print(f"[!] Failed to process {file}: {e}") 