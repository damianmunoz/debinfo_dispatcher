# dmd-module_translator/tests/astra_parser.py
from typing import List, Dict, Any

# Function to parse an SBOM in SPDX format and return a list of edges
# Parameters:
# - sbom: Dictionary representation of the SBOM in SPDX format
# Returns:
# - List of edges where each edge is a dictionary with keys: source_type, source_id
def parse_spdx(sbom: dict) -> List[Dict[str, str]]:
    edges = []
    creators = sbom.get('creationInfo', {}).get('creators', [])
    principal = None
    tools = []

    for creator in creators:
        if creator.startswith("Person:"):
            principal = creator.replace("Person:", "").strip() # Extract the principal's name
        elif creator.startswith("Tool:"): # Extract the tool's name
            tool_name = creator.replace("Tool:", "").strip() # Collect the tool's name
            tools.append(tool_name) # Collect all tools

    for tool in tools: # Iterate through the collected tools
        if principal:
            edges.append({
                "source_type": "Principal",
                "source_id": principal, # Use the principal's name
                "target_type": "Resource", 
                "target_id": tool, # Use the tool's name
                "relationship": "uses"
            })

    for pkg in sbom.get('packages', []): # Iterate through the packages
        artifact = pkg.get('name')
        supplier = pkg.get('supplier', '') # Get the supplier information
        if supplier.startswith("Organization:"): # Check if the supplier is an organization
            resource = supplier.replace("Organization:", "").strip() # Extract the organization name
            edges.append({ # Create an edge from the resource to the step
                "source_type": "Resource",
                "source_id": resource,
                "target_type": "Step",
                "target_id": "PackageImport",
                "relationship": "carries_out"
            })
            edges.append({ # Create an edge from the step to the artifact
                "source_type": "Step",
                "source_id": "PackageImport",
                "target_type": "Artifact",
                "target_id": artifact,
                "relationship": "produces"
            })

    return edges

# Function to parse an SBOM in CycloneDX format and return a list of edges
# Parameters:
# - sbom: Dictionary representation of the SBOM in CycloneDX format
# Returns:
# - List of edges where each edge is a dictionary with keys: source_type, source_id
#   target_type, target_id, relationship
# astra_parser.py

def parse_cyclonedx(sbom: Dict[str, Any]) -> List[Dict[str, str]]:
    edges = []
    metadata = sbom.get("metadata", {})
    timestamp = sbom.get("timestamp")
    components = sbom.get("components", [])
    dependencies = sbom.get("dependencies", [])

    principal = None
    tools = []

    # Extract principal and tools from metadata.authors or metadata.tools
    authors = metadata.get("authors", [])
    for author in authors:
        name = author.get("name")
        if name:
            if 'tool' in name.lower():
                tools.append(name.strip())
            else:
                principal = name.strip()

    tools_metadata = metadata.get("tools", [])
    for tool in tools_metadata:
        name = tool.get("name")
        if name:
            tools.append(name.strip())

    # Link Principal to Tools as Resources
    for tool in tools:
        if principal:
            edges.append({
                "source_type": "Principal",
                "source_id": principal,
                "target_type": "Resource",
                "target_id": tool,
                "relationship": "uses"
            })

    # Link Step to Artifacts
    for comp in components:
        artifact = comp.get("name")
        if artifact:
            edges.append({
                "source_type": "Step",
                "source_id": "ComponentDeclaration",
                "target_type": "Artifact",
                "target_id": artifact,
                "relationship": "produces"
            })

    # Optionally link dependencies (consumes relationship)
    for dep in dependencies:
        ref = dep.get("ref")
        for dep_ref in dep.get("dependsOn", []):
            edges.append({
                "source_type": "Artifact",
                "source_id": dep_ref,
                "target_type": "Artifact",
                "target_id": ref,
                "relationship": "is_dependency_of"
            })

    return edges