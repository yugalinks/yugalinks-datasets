# Yugalinks Dataset Catalog

This catalog helps people discover focused Yugalinks datasets for product, country, market, and exporter-importer research.

Each entry describes a useful view of reported international import-export data. It explains the subject, countries, products, years, available measures, and how the entry can be explored or downloaded. The catalog is a guide to the collection; it is not a replacement for the full source datasets.

## Files

- `catalog.jsonl`: one JSON object for each dataset entry.
- `catalog.schema.json`: the structure shared by catalog entries.
- `catalog-manifest.json`: collection coverage and release information.
- `generate_catalog.py`: a maintainer tool for refreshing the catalog.

## Current Preview

The current preview contains 10,000 selected exporter-product-buyer opportunity entries.

Selection rules:

- `lane_last_year >= 2022`
- `lane_data_years >= 5`
- `buyer_imports_latest_usd > 0`
- `addressable_proj_3y_usd > 0`

Each entry includes a stable identifier, a plain-language title, the countries and products involved, available years, measures, and access information. A projected value is an analytical estimate, not a promise of revenue.

## For Maintainers

Maintainers can refresh the catalog from the repository root:

```bash
python3 dataset-catalog/generate_catalog.py --limit 10000
```

The generated catalog is reviewed before any public release. Credentials and private data-access settings belong in the local runtime environment and must never be added to this repository or to public dataset descriptions.

## Explore the Data

Use each catalog entry to review its subject, coverage, measures, and access options before downloading or working with the data.

The Yugalinks website provides a readable page and preview for selected entries. Full historical files are available through the linked dataset releases.

The collection is based primarily on published OECD BIMTS data. Review each dataset's source notes and provider terms before redistribution or commercial use, and preserve the required citation and acknowledgement. Separately sourced context is identified on the relevant dataset page.
