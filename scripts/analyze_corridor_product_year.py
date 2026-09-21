"""Create a small corridor summary from a local Parquet sample or full file."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet", type=Path, help="Path to data.parquet or the GitHub sample.")
    parser.add_argument("--exporter", help="Optional exporter ISO3 filter.")
    parser.add_argument("--importer", help="Optional importer ISO3 filter.")
    parser.add_argument("--year", type=int, help="Optional year filter.")
    args = parser.parse_args()

    filters = []
    if args.exporter:
        filters.append(("exporter_iso3", args.exporter))
    if args.importer:
        filters.append(("importer_iso3", args.importer))
    if args.year:
        filters.append(("year", args.year))

    frame = pd.read_parquet(args.parquet)
    for column, value in filters:
        frame = frame[frame[column] == value]

    summary = (
        frame.groupby("hs_code", as_index=False)["export_value_usd"]
        .sum()
        .sort_values("export_value_usd", ascending=False)
        .head(20)
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
