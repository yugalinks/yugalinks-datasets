# Yugalinks Datasets

Yugalinks makes published international import-export data easier to find, understand, and use.

We prepare documented datasets for **MSMEs, researchers, developers, and analysts** who need to explore products, countries, markets, and exporter-importer corridors. The underlying observations remain attributed to their published sources; this repository provides the catalog, documentation, examples, and reproducible release metadata.

## Start Here

- [Browse the Yugalinks dataset collection on Hugging Face](https://huggingface.co/yugalinks/datasets)
- [Download the core corridor HS6 dataset](https://huggingface.co/datasets/yugalinks/import-export-corridor-product-year-v1)
- [Read the corridor dataset guide](datasets/corridor-product-year-v1.md)
- [Download the GitHub sample release](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.21-corridor-product-year-0001)
- [Explore the Yugalinks website](https://www.yugalinks.com)

## Core Dataset: Corridor Product Year

The core public dataset contains annual reported export values at this grain:

`year × exporter_iso3 × importer_iso3 × HS2017-6D product code`

It contains **312,010,945 rows** and is published as an **8.21 GB Parquet file** on Hugging Face. It is useful for finding product corridors, comparing destinations, studying historical movement, and building custom market-analysis tools.

The full file is intentionally hosted on Hugging Face rather than committed to Git. GitHub contains the documentation, schema, scripts, and a smaller sample for quick experiments.

## GitHub Sample

The [corridor sample release](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.21-corridor-product-year-0001) is designed for fast notebook and application testing. It is not a replacement for the complete dataset.

Use the sample to:

- Test Parquet loading and filtering.
- Build a first corridor or product chart.
- Validate schema handling before downloading the full file.
- Create a public example or tutorial without moving gigabytes of data.

## Reusable Tools

- [Dataset guide](datasets/corridor-product-year-v1.md) — purpose, grain, fields, provenance, and usage.
- [Download script](scripts/download_corridor_product_year.py) — fetch the canonical Parquet file from Hugging Face.
- [Analysis example](scripts/analyze_corridor_product_year.py) — create simple corridor and product summaries.
- [Logical dataset catalog](dataset-catalog/README.md) — browse the wider Yugalinks dataset definitions.
- [Catalog manifest](dataset-catalog/catalog-manifest.json) — machine-readable catalog metadata.
- [Catalog schema](dataset-catalog/catalog.schema.json) — structure of each catalog entry.
- [Dataset story template](templates/dataset-story-template.md) — reusable documentation structure.

Install the small local toolset with `pip install pandas pyarrow huggingface_hub`, then run:

```bash
python scripts/download_corridor_product_year.py --output-dir data
python scripts/analyze_corridor_product_year.py data/data.parquet --exporter IND --importer DEU
```

## Source and Attribution

The core corridor dataset is based primarily on the OECD Balanced International Merchandise Trade Statistics (BIMTS) HS2017-6D release. Derived growth fields are calculated from reported export values to support comparison and trend analysis.

Please retain OECD attribution when redistributing information from the datasets and review the applicable provider terms before commercial redistribution. Dataset cards document source coverage and limitations for each release.

## Collection Status

- Public Hugging Face datasets: 36
- Full Parquet files in this Git repository: no
- Full core corridor dataset: [Hugging Face](https://huggingface.co/datasets/yugalinks/import-export-corridor-product-year-v1)
- GitHub role: documentation, samples, scripts, catalog metadata, and release history
- Long-term citation archive: planned Zenodo release after the collection stabilizes

## About Yugalinks

Yugalinks turns published import-export data into practical resources that help people compare markets, understand product movement, and make better-informed international commerce decisions.

- [Website](https://www.yugalinks.com)
- [Hugging Face organization](https://huggingface.co/yugalinks)
- [GitHub organization](https://github.com/yugalinks)
