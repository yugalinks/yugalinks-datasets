#!/usr/bin/env python3
"""Generate a logical dataset catalog from qualified trade lanes.

The output is metadata only. It does not export the underlying trade rows.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DATABASE = "trade_gold_oecd_bimts_6d"
RISK_TABLE = "risk__lane_monitor_all__20260713"
HISTORY_TABLE = "oecd_bimts_6d__core__corridor_product_year__v1"
SOURCE_COVERAGE = "1995-2024"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    return parser.parse_args()


def clickhouse_url() -> str:
    host = os.getenv("CLICKHOUSE_HOST") or os.getenv("CLICKHOUSE_VM_HOST") or "127.0.0.1"
    if host == "host.docker.internal":
        host = "127.0.0.1"
    port = os.getenv("CLICKHOUSE_PORT", "8123")
    return f"http://{host}:{port}/"


def query_clickhouse(query: str) -> list[dict]:
    headers: dict[str, str] = {}
    user = os.getenv("CLICKHOUSE_USER")
    if user:
        headers["X-ClickHouse-User"] = user
        headers["X-ClickHouse-Key"] = os.getenv("CLICKHOUSE_PASSWORD", "")
    encoded = urllib.parse.urlencode({"query": query})
    request = urllib.request.Request(
        f"{clickhouse_url()}?{encoded}",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return [
            json.loads(line)
            for line in response.read().decode("utf-8").splitlines()
            if line.strip()
        ]


def catalog_query(limit: int) -> str:
    safe_limit = max(1, min(limit, 10000))
    return f"""
SELECT
    exporter_iso3,
    importer_iso3,
    hs_code,
    hs_description,
    lane_last_year,
    lane_data_years,
    addressable_proj_3y_usd
FROM {DATABASE}.{RISK_TABLE}
WHERE lane_last_year >= 2022
  AND lane_data_years >= 5
  AND buyer_imports_latest_usd > 0
  AND addressable_proj_3y_usd > 0
ORDER BY addressable_proj_3y_usd DESC, exporter_iso3, importer_iso3, hs_code
LIMIT {safe_limit}
FORMAT JSONEachRow
"""


def dataset_entry(row: dict, rank: int) -> dict:
    exporter = row["exporter_iso3"]
    importer = row["importer_iso3"]
    hs_code = row["hs_code"]
    dataset_id = f"trade-opportunity-lane-{exporter.lower()}-{importer.lower()}-{hs_code}"
    description = row.get("hs_description") or f"HS6 product {hs_code}"
    return {
        "dataset_id": dataset_id,
        "title": f"Trade opportunity lane: {description} from {exporter} to {importer}",
        "kind": "trade-opportunity-lane",
        "grain": "exporter_iso3 x importer_iso3 x hs_code",
        "filters": {
            "exporter_iso3": exporter,
            "importer_iso3": importer,
            "hs_code": hs_code,
        },
        "source": {
            "table": f"{DATABASE}.{RISK_TABLE}",
            "coverage": SOURCE_COVERAGE,
            "status": "derived",
        },
        "preview": {
            "rows": 1,
            "url": f"/datasets/{dataset_id}/preview",
        },
        "download": {
            "mode": "on-demand-filtered",
            "url": f"/datasets/{dataset_id}/download",
            "history_source": f"{DATABASE}.{HISTORY_TABLE}",
        },
        "rank": rank,
        "latest_year": row["lane_last_year"],
        "history_years": row["lane_data_years"],
        "estimated_addressable_3y_usd": row["addressable_proj_3y_usd"],
    }


def main() -> int:
    args = parse_args()
    if args.limit < 1 or args.limit > 10000:
        raise SystemExit("--limit must be between 1 and 10000")

    rows = query_clickhouse(catalog_query(args.limit))
    entries = [dataset_entry(row, index) for index, row in enumerate(rows, start=1)]
    ids = [entry["dataset_id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate dataset_id generated")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = output_dir / "catalog.jsonl"
    with catalog_path.open("w", encoding="utf-8") as output:
        for entry in entries:
            output.write(json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n")

    manifest = {
        "catalog_name": "Yugalinks Logical Trade Opportunity Dataset Catalog",
        "status": "preview",
        "logical_dataset_count": len(entries),
        "requested_dataset_count": args.limit,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_table": f"{DATABASE}.{RISK_TABLE}",
        "history_table": f"{DATABASE}.{HISTORY_TABLE}",
        "source_coverage": SOURCE_COVERAGE,
        "selection": {
            "lane_last_year_min": 2022,
            "lane_data_years_min": 5,
            "buyer_imports_latest_usd": "positive",
            "addressable_proj_3y_usd": "positive",
        },
        "files": {
            "catalog": "catalog.jsonl",
            "schema": "catalog.schema.json",
            "readme": "README.md",
        },
        "data_rows_exported": False,
    }
    (output_dir / "catalog-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
