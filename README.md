# Yugalinks Datasets

Public GitHub catalog for Yugalinks AI-ready trade datasets.

This repository currently contains a preview catalog, not a copy of the full ClickHouse trade warehouse. The catalog contains 10,000 logical dataset definitions backed by shared, versioned trade data.

## Start Here

- [Logical dataset catalog](dataset-catalog/README.md)
- [Catalog manifest](dataset-catalog/catalog-manifest.json)
- [Catalog schema](dataset-catalog/catalog.schema.json)
- [10,000 dataset definitions](dataset-catalog/catalog.jsonl)
- [Reproducible generator](dataset-catalog/generate_catalog.py)

Each catalog entry identifies a trade lane, its grain, source version, filters, preview route, and on-demand download contract. The entries are metadata-only in this preview; no 312M-row archive is included.

## Status

- Catalog status: preview
- Logical dataset definitions: 10,000
- Full data rows included: no
- Public platform uploads: not yet
- OECD-derived redistribution terms: pending review
