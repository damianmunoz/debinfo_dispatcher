# debinfo/deb_astra.py

import json
import os
import re

# Load the .buildinfo file
input_file = "debinfo/testdeb.txt"
output_file = "viewer/deb_graph.json"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

nodes = []
links = []

# Helper sets to prevent duplicates
node_ids = set()
added_links = set()

def add_node(id_, group):
    if id_ not in node_ids:
        nodes.append({"id": id_, "group": group})
        node_ids.add(id_)

def add_link(src, dst, label):
    key = (src, dst, label)
    if key not in added_links:
        links.append({"source": src, "target": dst, "label": label})
        added_links.add(key)

# --- Extract metadata ---

builder = None
source_artifact = None
build_step = "Step::DebianBuild"
output_artifact = None
resources = []

for line in lines:
    line = line.strip()

    if line.startswith("Build-Origin:"):
        builder = line.split(":", 1)[1].strip() 

    elif line.startswith("Source:"):
        source_artifact = "Artifact::Source::" + line.split(":", 1)[1].strip()

    elif line.startswith("Build-Architecture:"):
        arch = line.split(":", 1)[1].strip()
        output_artifact = f"Artifact::Output::{arch}"

    elif re.match(r"^\s*\S+\s+\S+\s+.+$", line):
        # Probably a resource line (checksum type + hash + filename)
        parts = line.split()
        if len(parts) >= 3:
            res = "Resource::" + parts[2]
            resources.append(res)

# --- Add nodes and links ---

# Principal (builder)
if builder:
    principal_node = f"Principal::{builder}"
    add_node(principal_node, "Principal")
    add_node(build_step, "Step")
    add_link(principal_node, build_step, "carries_out")

# Step
add_node(build_step, "Step")

# Source artifact
if source_artifact:
    add_node(source_artifact, "Artifact")
    add_link(build_step, source_artifact, "consumes")

# Output artifact
if output_artifact:
    add_node(output_artifact, "Artifact")
    add_link(build_step, output_artifact, "produces")

# Resources
for res in resources:
    add_node(res, "Resource")
    add_link(res, build_step, "used_by")

# Write JSON graph for 3D viewer
graph = {"nodes": nodes, "links": links}
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(graph, f, indent=2)

print(f"[✓] DAG written to {output_file}")
