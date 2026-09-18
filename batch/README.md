# Batch Generator

`generate_batch.py` turns catalog definitions into complete local dataset packages.

Each package contains:

- `snapshot.parquet`: the current derived opportunity/risk record.
- `history.parquet`: observed exporter/importer/HS6 trade history.
- `metadata.json`: filters, source tables, coverage, and file metadata.
- `README.md`: user-facing explanation and field treatment.

The default batch reads the first 10 catalog entries. It writes to `releases/`, which is intentionally ignored by Git so source-derived rows cannot be committed accidentally.

Run locally with ClickHouse credentials loaded in the environment:

```bash
python3 batch/generate_batch.py --limit 10
```

This creates a private local artifact. Public release requires a reviewed redistribution decision.
