#!/usr/bin/env python3
"""Generate complete local packages for catalog entries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DATABASE = "trade_gold_oecd_bimts_6d"
RISK_TABLE = "risk__lane_monitor_all__20260713"
HISTORY_TABLE = "oecd_bimts_6d__core__corridor_product_year__v1"
CATALOG_PATH = Path(__file__).resolve().parent.parent / "dataset-catalog" / "catalog.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "releases" / "batch-0001",
    )
    return parser.parse_args()


def clickhouse_url() -> str:
    host = os.getenv("CLICKHOUSE_HOST") or os.getenv("CLICKHOUSE_VM_HOST") or "127.0.0.1"
    if host == "host.docker.internal":
        host = "127.0.0.1"
    return f"http://{host}:{os.getenv('CLICKHOUSE_PORT', '8123')}/"


def clickhouse_request(query: str) -> urllib.request.addinfourl:
    headers: dict[str, str] = {}
    user = os.getenv("CLICKHOUSE_USER")
    if user:
        headers["X-ClickHouse-User"] = user
        headers["X-ClickHouse-Key"] = os.getenv("CLICKHOUSE_PASSWORD", "")
    params = urllib.parse.urlencode({"query": query})
    request = urllib.request.Request(f"{clickhouse_url()}?{params}", headers=headers)
    return urllib.request.urlopen(request, timeout=180)


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def read_catalog(limit: int) -> list[dict]:
    entries: list[dict] = []
    with CATALOG_PATH.open(encoding="utf-8") as catalog:
        for line in catalog:
            if line.strip():
                entries.append(json.loads(line))
            if len(entries) == limit:
                break
    if len(entries) != limit:
        raise SystemExit(f"Catalog contains only {len(entries)} entries; requested {limit}")
    return entries


def export_parquet(query: str, destination: Path) -> None:
    with clickhouse_request(query) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def count_rows(query: str) -> int:
    with clickhouse_request(query + " FORMAT JSONEachRow") as response:
        payload = json.loads(response.read().decode("utf-8").strip())
    return int(payload["rows"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_package(entry: dict, package: Path) -> dict:
    package.mkdir(parents=True, exist_ok=True)
    filters = entry["filters"]
    exporter = sql_literal(filters["exporter_iso3"])
    importer = sql_literal(filters["importer_iso3"])
    hs_code = sql_literal(filters["hs_code"])
    where = f"exporter_iso3 = {exporter} AND importer_iso3 = {importer} AND hs_code = {hs_code}"

    snapshot_count_query = f"SELECT count() AS rows FROM {DATABASE}.{RISK_TABLE} WHERE {where}"
    history_count_query = f"SELECT count() AS rows FROM {DATABASE}.{HISTORY_TABLE} WHERE {where}"
    snapshot_query = f"SELECT * FROM {DATABASE}.{RISK_TABLE} WHERE {where} FORMAT Parquet"
    history_query = (
        f"SELECT year, exporter_iso3, importer_iso3, hs_code, export_value_usd, yoy_growth_pct, cagr_3y_pct "
        f"FROM {DATABASE}.{HISTORY_TABLE} WHERE {where} ORDER BY year FORMAT Parquet"
    )

    snapshot = package / "snapshot.parquet"
    history = package / "history.parquet"
    export_parquet(snapshot_query, snapshot)
    export_parquet(history_query, history)

    files = [
        {
            "path": snapshot.name,
            "expected_rows": count_rows(snapshot_count_query),
            "bytes": snapshot.stat().st_size,
            "sha256": sha256(snapshot),
        },
        {
            "path": history.name,
            "expected_rows": count_rows(history_count_query),
            "bytes": history.stat().st_size,
            "sha256": sha256(history),
        },
    ]
    metadata = {
        "dataset": entry,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "local-private-preview",
        "source_tables": [f"{DATABASE}.{RISK_TABLE}", f"{DATABASE}.{HISTORY_TABLE}"],
        "coverage": "1995-2024",
        "files": files,
        "license_status": "review-required",
        "data_rows_are_public": False,
    }
    (package / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (package / "README.md").write_text(
        f"# {entry['title']}\n\n"
        "This package contains a current derived opportunity/risk snapshot and the corresponding observed trade history.\n\n"
        f"- Dataset ID: `{entry['dataset_id']}`\n"
        f"- Grain: `{entry['grain']}`\n"
        f"- Coverage: `1995-2024`\n"
        "- Projected values are estimates, not guaranteed revenue.\n"
        "- Redistribution terms require review before public release.\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    args = parse_args()
    if not 1 <= args.limit <= 100:
        raise SystemExit("--limit must be between 1 and 100")
    entries = read_catalog(args.limit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packages = [
        build_package(entry, args.output_dir / entry["dataset_id"])
        for entry in entries
    ]
    manifest = {
        "batch_id": "batch-0001",
        "status": "local-private-preview",
        "dataset_count": len(packages),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "data_rows_are_public": False,
        "license_status": "review-required",
        "packages": [package["dataset"]["dataset_id"] for package in packages],
    }
    (args.output_dir / "batch-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
