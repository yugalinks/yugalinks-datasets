# Batch Generator

`generate_batch.py` turns catalog definitions into complete local dataset packages.

Each package contains:

- `snapshot.parquet`: the current derived opportunity/risk record.
- `history.parquet`: observed exporter/importer/HS6 trade history.
- `metadata.json`: filters, source tables, coverage, and file metadata.
- `README.md`: user-facing explanation and field treatment.

The default batch reads the first 10 catalog entries. It writes to `releases/`, which is intentionally ignored by Git so generated data is released through an explicit versioned release rather than committed accidentally.

Run locally with ClickHouse credentials loaded in the environment:

```bash
python3 batch/generate_batch.py --limit 10
```

This creates a local OECD-only artifact. The package includes the OECD Terms & Conditions, citation, and acknowledgement. Separately sourced macro, tariff, distance, and language context is excluded from this batch.

## PSEO T17 Sample

`generate_t17_package.py` creates a small OECD-derived exporter opportunity package from the T17 source grain. It defaults to 50 ranked opportunities for China and excludes separately sourced macro, access, language, and institutional context.

```bash
python3 batch/generate_t17_package.py --exporter CHN --limit 50
```
