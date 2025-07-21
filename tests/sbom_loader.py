# sbom_loader.py
import json
import os
from typing import Union, Dict, Any
from datetime import datetime


def detect_format(sbom_path: str) -> str:
    with open(sbom_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if 'spdxVersion' in data:
                return 'spdx'
            elif 'bomFormat' in data and data['bomFormat'].lower() == 'cyclonedx':
                return 'cyclonedx-json'
        except json.JSONDecodeError:
            pass

    ext = os.path.splitext(sbom_path)[1].lower()
    if ext.endswith('.spdx') or ext.endswith('.spdx.json'):
        return 'spdx'
    elif ext.endswith('.cdx.json') or ext.endswith('.sbom.json') or ext.endswith('.json'):
        return 'cyclonedx-json'

    raise ValueError(f"[!] Unsupported or invalid SBOM format in file: {sbom_path}")


def load_sbom(sbom_path: str) -> Dict[str, Any]:
    fmt = detect_format(sbom_path)
    if fmt != 'cyclonedx-json':
        raise ValueError(f"[!] Only CycloneDX JSON format is currently supported. Got: {fmt}")

    with open(sbom_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    result = {
        "components": data.get("components", []),
        "dependencies": data.get("dependencies", []),
        "metadata": data.get("metadata", {}),
        "services": data.get("services", []),
        "externalReferences": data.get("externalReferences", []),
        "timestamp": None,
        "raw": data
    }

    # Parse timestamp if available
    timestamp = result["metadata"].get("timestamp")
    if timestamp:
        try:
            result["timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except Exception:
            result["timestamp"] = timestamp

    return result
