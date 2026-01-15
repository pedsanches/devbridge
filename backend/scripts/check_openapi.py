"""OpenAPI contract checker.

Compares generated FastAPI OpenAPI schema with the versioned YAML spec.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "docs" / "api" / "openapi.yaml"


def load_versioned_spec() -> dict[str, Any]:
    """Load the versioned OpenAPI spec from disk."""
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"OpenAPI spec not found at {SPEC_PATH}")
    with SPEC_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("OpenAPI spec must be a YAML mapping")
    return data


def generate_openapi() -> dict[str, Any]:
    """Generate the OpenAPI spec from the FastAPI app."""
    spec = app.openapi()
    if not isinstance(spec, dict):
        raise ValueError("Generated OpenAPI spec is invalid")
    return spec


def normalize(data: dict[str, Any]) -> str:
    """Normalize JSON for comparison."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def dump_yaml(data: dict[str, Any]) -> str:
    """Serialize OpenAPI spec to YAML."""
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OpenAPI spec against source")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite docs/api/openapi.yaml with generated spec",
    )
    args = parser.parse_args()

    generated = generate_openapi()
    versioned = load_versioned_spec()

    if normalize(generated) == normalize(versioned):
        print("OpenAPI spec is up to date.")
        return 0

    if args.write:
        SPEC_PATH.write_text(dump_yaml(generated), encoding="utf-8")
        print("OpenAPI spec updated.")
        return 0

    print("OpenAPI spec is out of sync. Run: make openapi-sync", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
