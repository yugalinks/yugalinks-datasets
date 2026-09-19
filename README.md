# Yugalinks Datasets

Public GitHub catalog for Yugalinks AI-ready trade datasets.

This repository currently contains a preview catalog, not a copy of the full ClickHouse trade warehouse. The catalog contains 10,000 logical dataset definitions backed by shared, versioned trade data.

## Start Here

- [Logical dataset catalog](dataset-catalog/README.md)
- [Catalog manifest](dataset-catalog/catalog-manifest.json)
- [Catalog schema](dataset-catalog/catalog.schema.json)
- [10,000-dataset allocation plan](dataset-catalog/allocation-plan.json)
- [PSEO dataset opportunities](dataset-catalog/pseo-opportunities.json)
- [PSEO package manifest](dataset-catalog/pseo-package-manifest.json)
- [10,000 dataset definitions](dataset-catalog/catalog.jsonl)
- [Reproducible generator](dataset-catalog/generate_catalog.py)
- [First-batch generator](batch/README.md)
- [Dataset story template](templates/dataset-story-template.md)

Each catalog entry identifies a trade lane, its grain, source version, filters, preview route, and on-demand download contract. The entries are metadata-only in this preview; no 312M-row archive is included.

## Download Batch 0001

- [Open the release page](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.18-batch-0001)
- [Download all 10 datasets](https://github.com/yugalinks/yugalinks-datasets/releases/download/v2026.09.18-batch-0001/yugalinks-oecd-trade-batch-0001.zip)
- [Download the Sweden-China HS6 example](https://github.com/yugalinks/yugalinks-datasets/releases/download/v2026.09.18-batch-0001/trade-opportunity-lane-swe-chn-260111.zip)

The release page contains the individual download for every dataset in the batch. Downloads are public and do not require a GitHub account.

## PSEO T17 Sample

- [Open the PSEO T17 sample release](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.19-pseo-t17-0001)
- [Download the 50-row China exporter opportunity sample](https://github.com/yugalinks/yugalinks-datasets/releases/download/v2026.09.19-pseo-t17-0001/pseo-t17-exporter-chn-0001.zip)
- [Generate the sample locally](batch/README.md#pseo-t17-sample)

This sample contains 50 ranked OECD-derived opportunity rows from 525,076 qualifying China opportunities. It is a validation sample, not the complete opportunity universe.

## 50,000 Gold-Marts Catalog

- [Open the 50,000-product release](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.19-gold-50000-0001)
- [Download the grouped catalog ZIP](https://github.com/yugalinks/yugalinks-datasets/releases/download/v2026.09.19-gold-50000-0001/top-50000-gold-catalog.zip)
- [Download the actual 50,000-row Parquet dataset](https://github.com/yugalinks/yugalinks-datasets/releases/download/v2026.09.19-gold-50000-0001/selected_gold_rows.parquet)
- [Download the 50,000-entry catalog JSONL](https://github.com/yugalinks/yugalinks-datasets/releases/download/v2026.09.19-gold-50000-0001/catalog.jsonl)
- [Generate it locally](batch/README.md#50000-gold-marts-catalog)

This release contains 50,000 logical dataset entries and 50,000 selected source rows distributed across 12 gold-mart algorithm families. It is one grouped collection, not 50,000 separate platform listings.

## Status

- Catalog status: preview
- Logical dataset definitions: 10,000
- Full data rows in the Git repository: no
- Public GitHub release: `v2026.09.18-batch-0001`
- Kaggle/Hugging Face/Zenodo uploads: not yet
- OECD BIMTS terms: permitted under OECD Terms & Conditions with attribution
- Separately sourced context: excluded from the first batch pending source review

The public `v2026.09.18-batch-0001` release contains 10 complete lane packages with current snapshots and observed history. The Parquet files are attached to the GitHub Release instead of being duplicated in the Git tree.
