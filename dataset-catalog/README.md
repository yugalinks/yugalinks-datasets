# Yugalinks Logical Dataset Catalog

This directory is a GitHub-first preview of the scalable dataset model.

It is a catalog of logical dataset definitions, not a copy of the 312M-row trade tables. Each catalog entry describes one useful filtered dataset that can be previewed and downloaded from a shared partitioned archive or retrieved through a parameterized API query.

## Files

- `catalog.jsonl`: one JSON object per logical dataset.
- `catalog.schema.json`: JSON Schema for every catalog entry.
- `catalog-manifest.json`: generation metadata and selection rules.
- `generate_catalog.py`: reproducible generator using local ClickHouse metadata/data.

## Current Preview

The default generator creates 10,000 qualified exporter-product-buyer opportunity-lane definitions from `risk__lane_monitor_all__20260713`.

Selection rules:

- `lane_last_year >= 2022`
- `lane_data_years >= 5`
- `buyer_imports_latest_usd > 0`
- `addressable_proj_3y_usd > 0`

Each entry has a stable lane identifier, title, grain, filters, source table, source coverage, estimated preview size, and an on-demand download contract. It does not claim that a projected value is guaranteed revenue.

## Regenerate

Run this from the repository root with local ClickHouse available:

```bash
python3 dataset-catalog/generate_catalog.py --limit 10000
```

The script reads `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_USER`, and `CLICKHOUSE_PASSWORD` from the environment when provided. It does not publish data to Kaggle, Hugging Face, Zenodo, or a public API.

## Intended Distribution

- GitHub stores the catalog definition, schema, generator, and release metadata.
- Yugalinks exposes one page and preview per logical dataset.
- The download service resolves a catalog filter to shared Parquet partitions or a bounded query.
- Full historical archives remain available as partitioned advanced downloads rather than being copied into every logical dataset.

OECD BIMTS files can be redistributed under the OECD Terms & Conditions when the required citation and acknowledgement are preserved. Separately sourced context fields require their own source review and are excluded from the first public batch.
