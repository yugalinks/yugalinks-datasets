# Yugalinks Datasets

Public GitHub catalog for Yugalinks AI-ready trade datasets.

This repository currently contains a preview catalog, not a copy of the full ClickHouse trade warehouse. The catalog contains 10,000 logical dataset definitions backed by shared, versioned trade data.

## Start Here

- [Logical dataset catalog](dataset-catalog/README.md)
- [Catalog manifest](dataset-catalog/catalog-manifest.json)
- [Catalog schema](dataset-catalog/catalog.schema.json)
- [10,000 dataset definitions](dataset-catalog/catalog.jsonl)
- [Reproducible generator](dataset-catalog/generate_catalog.py)
- [First-batch generator](batch/README.md)

Each catalog entry identifies a trade lane, its grain, source version, filters, preview route, and on-demand download contract. The entries are metadata-only in this preview; no 312M-row archive is included.

## Status

- Catalog status: preview
- Logical dataset definitions: 10,000
- Full data rows in the Git repository: no
- Public GitHub release: `v2026.09.18-batch-0001`
- Kaggle/Hugging Face/Zenodo uploads: not yet
- OECD BIMTS terms: permitted under OECD Terms & Conditions with attribution
- Separately sourced context: excluded from the first batch pending source review

The first local batch generator creates 10 complete lane packages with a current snapshot and observed history. Generated Parquet files are intentionally ignored by Git until redistribution terms are reviewed.
