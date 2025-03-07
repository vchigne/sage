"""
SAGE Schema Definitions

This package contains the schema definitions and validation logic for YAML files
used in SAGE (Structured Automated Governance of Entities).

Available schemas:
- CatalogSchema: Validates catalog.yaml files
- PackageSchema: Validates package.yaml files
- SenderSchema: Validates sender.yaml files
"""

from .catalog import CatalogSchema
from .package import PackageSchema
from .sender import SenderSchema

__all__ = ['CatalogSchema', 'PackageSchema', 'SenderSchema']
