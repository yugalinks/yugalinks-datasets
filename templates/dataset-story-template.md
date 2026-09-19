# [Exporter] to [Importer] [Product] Trade Dataset

## One-Sentence Summary

This dataset shows how reported trade for [product and HS6 code] changed between [first year] and [last year] on the [exporter] to [importer] lane.

## Why This Matters

Use this dataset to answer:

- Did trade on this lane grow, decline, or stop?
- What was the latest reported trade value?
- How many years of observations are available?
- Is the lane concentrated or volatile?
- What should a researcher check next?

Do not describe a projection as guaranteed revenue or call a calculated ranking an observed fact.

## What Is Included

| File | Grain | Expected rows |
|---|---|---:|
| `snapshot.parquet` | One current lane record | [count] |
| `history.parquet` | Exporter x importer x HS6 x year | [count] |
| `metadata.json` | Source, filters, coverage, and checksums | 1 |

The natural row count is more important than an arbitrary minimum. A single lane may have 5-30 historical rows. Do not pad a dataset with unrelated rows just to reach 100.

## Data Snapshot

- Exporter: [country and ISO3]
- Importer: [country and ISO3]
- Product: [HS6 code and description]
- Latest reported year: [year]
- Historical observations: [count]
- Latest reported trade value: [value and currency]

## Quick Example

```python
import pandas as pd

history = pd.read_parquet("history.parquet")
print(history.sort_values("year").tail())
```

## Source And Terms

Primary source: OECD (2025), Balanced international merchandise trade statistics (BIMTS) - HS2017-6D, OECD Data Explorer.

Terms: OECD Terms & Conditions. Preserve the OECD citation and acknowledgement when redistributing this dataset.

## Field Treatment

- Reported trade values are observed source data.
- Growth, share, volatility, concentration, and opportunity values are calculated or derived.
- Projections are estimates and are not guarantees.

## Limitations

- Coverage and observations vary by country, product, and year.
- Missing years do not mean that trade was zero.
- This dataset is a research aid, not financial, legal, or customs advice.

## Related Datasets

- [Product-market dataset]
- [Corridor history dataset]
- [Risk monitor dataset]
- [Full catalog]
