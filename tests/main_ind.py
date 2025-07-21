# main.py
import os
import sys
from sbom_loader import load_sbom
from astra_parser import parse_cyclonedx
from catalog_writer import write_catalog
from graph_writer import write_graph_json

def main(sbom_path: str):
    try:
        sbom = load_sbom(sbom_path)
        print(f"[+] Loaded SBOM from {sbom_path}")

        edges = parse_cyclonedx(sbom)
        print(f"[+] Parsed {len(edges)} edges from SBOM")

        # Save to output directory
        base_name = os.path.splitext(os.path.basename(sbom_path))[0]
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_csv = os.path.join(output_dir, base_name + "_astra_catalog.csv")

        write_catalog(edges, output_csv)
        
        graph_json_path = os.path.join(output_dir, base_name + "_graph.json")
        write_graph_json(edges, graph_json_path)


    except Exception as e:
        print(f"[!] Failed to process {sbom_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <sbom-file-path>")
        sys.exit(1)

    sbom_file = sys.argv[1]
    main(sbom_file)
