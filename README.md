# AStRA MVP Module

This module extracts and catalogs relationships from SBOMs (Software Bill of Materials) according to the AStRA model defined in *"SoK: A Defense-Oriented Evaluation of Software Supply Chain Security"*.

## What It Does

It reads SBOM files in either SPDX or CycloneDX JSON format and outputs AStRA-style relationships as edges in a graph. These relationships represent:

- **Principals** (e.g., authors or maintainers)
- **Resources** (e.g., tools or suppliers)
- **Steps** (e.g., build or import actions)
- **Artifacts** (e.g., packages or components)

Each relationship is expressed as a directed edge like:

Principal → uses → Resource
Resource → carries_out → Step
Step → produces → Artifact


##  Directory Structure

- `main.py`: Entry point for processing SBOM files
- `sbom_loader.py`: Detects SBOM format and loads content
- `astra_parser.py`: Transforms SPDX/CycloneDX SBOM into AStRA relationships
- `catalog_writer.py`: Writes output relationships to CSV

##  Usage

From the `tests/` folder:
```bash
python main.py ../sbom_data/bom-shelter/in-the-wild/cyclonedx/some_file.json