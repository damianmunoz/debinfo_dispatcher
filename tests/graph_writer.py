import json
from typing import List, Dict

# This script writes a graph structure to a JSON file.
# The graph consists of nodes and edges, where each edge connects two nodes
# and has a relationship type.
def write_graph_json(edges: List[Dict[str, str]], output_path: str):
    nodes = {}
    links = []

    for edge in edges:
        src_id = f"{edge['source_type']}::{edge['source_id']}"
        tgt_id = f"{edge['target_type']}::{edge['target_id']}"

        # Register nodes
        for node_id, node_type in [(src_id, edge['source_type']), (tgt_id, edge['target_type'])]:
            if node_id not in nodes:
                nodes[node_id] = {"id": node_id, "group": node_type}

        # Add link
        links.append({
            "source": src_id,
            "target": tgt_id,
            "label": edge['relationship']
        })

    graph = {
        "nodes": list(nodes.values()),
        "links": links
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

    print(f"[+] Wrote graph JSON to {output_path}")
