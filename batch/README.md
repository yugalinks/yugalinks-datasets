# Dataset Packaging Tools

This directory contains maintainer tools for preparing optional example data packages. Public users should start with the [main dataset guide](../README.md) and the published dataset cards.

`generate_batch.py` turns selected catalog entries into complete local packages.

Each package contains:

- `snapshot.parquet`: the current derived opportunity/risk record.
- `history.parquet`: observed exporter/importer/HS6 trade history.
- `metadata.json`: selected filters, coverage, sources, and file details.
- `README.md`: user-facing explanation and field treatment.

The default batch reads the first 10 catalog entries. It writes to `releases/`, which is intentionally ignored by Git so generated data is released through an explicit versioned release rather than committed accidentally.

Run locally with the required private data-access settings loaded in the environment:

```bash
python3 batch/generate_batch.py --limit 10
```

This creates a local OECD-only artifact. The package includes the OECD Terms & Conditions, citation, and acknowledgement. Separately sourced macro, tariff, distance, and language context is excluded from this batch.

## PSEO T17 Sample

`generate_t17_package.py` creates a small OECD-derived exporter opportunity package from the T17 dataset definition. It defaults to 50 ranked opportunities for China and excludes separately sourced macro, access, language, and institutional context.

```bash
python3 batch/generate_t17_package.py --exporter CHN --limit 50
```

## 50,000-Product Catalog

`generate_50000_gold_catalog.py` selects a balanced collection of 50,000 products across the available published dataset families. It writes one JSONL catalog and one normalized Parquet collection to `releases/top-50000-gold-catalog/`.

```bash
python3 batch/generate_50000_gold_catalog.py
```
