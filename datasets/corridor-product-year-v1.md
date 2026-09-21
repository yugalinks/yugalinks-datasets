# Yugalinks Import-Export Corridor Product Year HS6 Flows v1

The core Yugalinks corridor dataset contains annual reported export values by exporter, importer, HS2017-6D product code, and year.

## Why it matters

This is the most reusable foundation in the collection for MSMEs, analysts, researchers, and developers. It can support questions such as:

- Which destinations buy a particular HS6 product?
- Which products move between two countries?
- How has a corridor changed across years?
- Which exporter-importer-product combinations have the largest reported value?

## Row grain

Each row represents one:

- Calendar year
- Exporter country (`exporter_iso3`)
- Importer country (`importer_iso3`)
- HS2017-6D product code (`hs_code`)

The dataset contains **312,010,945 rows**. The complete Parquet file is approximately **8.21 GB**.

## Fields

| Field | Meaning |
| --- | --- |
| `year` | Calendar year of the observation. |
| `exporter_iso3` | ISO3 code for the exporting country. |
| `importer_iso3` | ISO3 code for the importing country. |
| `hs_code` | HS2017-6D product code. |
| `export_value_usd` | Reported FOB export value in US dollars. |
| `yoy_growth_pct` | Year-on-year percentage change where available. |
| `cagr_3y_pct` | Three-year compound annual growth rate where available. |

## Files and downloads

- [Complete dataset on Hugging Face](https://huggingface.co/datasets/yugalinks/import-export-corridor-product-year-v1)
- [Direct Parquet download](https://huggingface.co/datasets/yugalinks/import-export-corridor-product-year-v1/resolve/main/data.parquet)
- [Small GitHub sample release](https://github.com/yugalinks/yugalinks-datasets/releases/tag/v2026.09.21-corridor-product-year-0001)
- [Manifest and checksum on Hugging Face](https://huggingface.co/datasets/yugalinks/import-export-corridor-product-year-v1/blob/main/manifest.json)

## Python

```python
import pandas as pd

frame = pd.read_parquet("data.parquet")

india_to_germany = frame[
    (frame["exporter_iso3"] == "IND")
    & (frame["importer_iso3"] == "DEU")
]

top_products = (
    india_to_germany.groupby("hs_code", as_index=False)["export_value_usd"]
    .sum()
    .sort_values("export_value_usd", ascending=False)
    .head(20)
)
```

For a quick test, download the GitHub sample before fetching the complete file.

## Provenance and interpretation

Reported country, product, year, and value observations are based primarily on the OECD Balanced International Merchandise Trade Statistics (BIMTS) HS2017-6D release. The corridor view aggregates reported observations by exporter, importer, HS6 product, and year.

Growth fields are derived indicators for comparison. They are not forecasts and do not guarantee future demand, prices, or commercial success. A reported export value is evidence of historical activity, not a promise of an available buyer or an easy market entry.

## Attribution

Please retain OECD attribution when redistributing this dataset and review the applicable OECD provider terms before commercial redistribution.

## Related links

- [Yugalinks on Hugging Face](https://huggingface.co/yugalinks)
- [Yugalinks website](https://www.yugalinks.com)
- [Yugalinks GitHub datasets](https://github.com/yugalinks/yugalinks-datasets)
