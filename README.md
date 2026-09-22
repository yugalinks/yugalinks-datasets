# Yugalinks Datasets

Yugalinks publishes documented international import-export data that helps people compare products, countries, markets, and exporter-importer routes.

The collection is useful for **MSMEs, researchers, developers, educators, and analysts**. Each dataset explains what it contains, which years and countries are represented, how its fields should be read, and which provider terms apply.

## Explore the Collection

- [Browse all Yugalinks datasets on Hugging Face](https://huggingface.co/yugalinks/datasets)
- [Open the core corridor dataset](https://huggingface.co/datasets/yugalinks/import-export-corridor-product-year-v1)
- [Read the core dataset guide](datasets/corridor-product-year-v1.md)
- [Download the GitHub sample](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.21-corridor-product-year-0001)
- [Open the Yugalinks website](https://www.yugalinks.com)

## Core Corridor Dataset

The core dataset records reported annual export values for:

- The year of the observation
- The exporting country
- The importing country
- The HS2017-6D product code

It contains **312,010,945 observations** covering **1995-2024**. Download the complete **8.21 GB Parquet file** from Hugging Face to compare destinations, study product movement, identify active corridors, and build your own research or analysis tools.

The field guide, examples, download helper, and smaller sample below can help you understand the data before working with the complete file.

## Start With the Sample

The [corridor sample release](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.21-corridor-product-year-0001) is a lightweight way to learn the file structure before downloading the full dataset.

Use it to:

- Open a Parquet file in a notebook
- Try a country, product, or corridor filter
- Create a first chart or summary
- Build a public tutorial without downloading gigabytes of data

The sample is for exploration and testing. Use the complete Hugging Face file for full historical analysis.

## Helpful Resources

- [Core dataset guide](datasets/corridor-product-year-v1.md) — coverage, fields, sources, and examples
- [Download helper](scripts/download_corridor_product_year.py) — download the complete core file
- [Analysis example](scripts/analyze_corridor_product_year.py) — create corridor and product summaries
- [Dataset catalog](dataset-catalog/README.md) — explore additional dataset definitions
- [Catalog manifest](dataset-catalog/catalog-manifest.json) — machine-readable collection information
- [Catalog schema](dataset-catalog/catalog.schema.json) — structure of catalog entries
- [Dataset documentation template](templates/dataset-story-template.md) — a reusable guide to describing a dataset

Install the small Python toolset with `pip install pandas pyarrow huggingface_hub`, then run:

```bash
python scripts/download_corridor_product_year.py --output-dir data
python scripts/analyze_corridor_product_year.py data/data.parquet --exporter IND --importer DEU
```

## Sources and Use

The core corridor dataset is based primarily on the OECD Balanced International Merchandise Trade Statistics (BIMTS) HS2017-6D release. Derived fields are documented on the dataset card and are intended for comparison and research.

Reported trade data reflects published observations. Coverage differs between datasets, and a calculated indicator should not be treated as a guaranteed forecast or recommendation. Review the source notes and provider terms before redistribution or commercial use, and retain the required OECD attribution.

The collection includes **36 public datasets**. Each dataset manifest includes its version-specific Zenodo citation DOI.

## About Yugalinks

Yugalinks turns published import-export data into practical resources that help people understand international commerce and make better-informed research and business decisions.

- [Website](https://www.yugalinks.com)
- [Hugging Face organization](https://huggingface.co/yugalinks)
- [GitHub organization](https://github.com/yugalinks)
- [Contact Yugalinks](mailto:info@yugalinks.com)
