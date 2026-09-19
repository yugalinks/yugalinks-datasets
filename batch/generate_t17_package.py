#!/usr/bin/env python3
"""Generate a small OECD-derived T17 exporter opportunity package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as parquet


TABLE = "trade_gold_oecd_bimts_6d.msme__serve__opportunity"
TERMS_URL = "https://www.oecd.org/termsandconditions/"
SOURCE_URL = "https://data-explorer.oecd.org/"
DATAFLOW_URL = "https://sdmx.oecd.org/sti-public/rest/dataflow/OECD.SDD.TPS/DSD_BIMTS_6D@DF_BIMTS_HS2017_6D/1.0"
CITATION = "OECD (2025), Balanced international merchandise trade statistics (BIMTS) - HS2017-6D"
MIN_BUYER_IMPORTS_USD = 50_000
MIN_LANE_YEARS = 3

# These fields are trade observations or calculations based on those observations.
# Macro, access, language, distance, and institutional context fields are excluded.
OECD_DERIVED_COLUMNS = (
    "exporter_iso3",
    "importer_iso3",
    "hs_code",
    "hs_description",
    "hs_chapter",
    "hs_heading",
    "buyer_imports_latest_usd",
    "buyer_imports_avg_usd",
    "buyer_imports_peak_usd",
    "buyer_cagr_full_pct",
    "buyer_yoy_avg_pct",
    "buyer_yoy_latest_pct",
    "buyer_trend_consistency_pct",
    "buyer_imports_proj_3y_usd",
    "buyer_imports_proj_5y_usd",
    "exports_latest_usd",
    "exports_avg_usd",
    "exports_peak_usd",
    "share_latest_pct",
    "share_avg_pct",
    "share_peak_pct",
    "share_change_1y_pp",
    "share_trend_pp_per_yr",
    "cagr_full_pct",
    "yoy_avg_pct",
    "yoy_latest_pct",
    "trend_consistency_pct",
    "exports_proj_3y_usd",
    "exports_proj_5y_usd",
    "your_share_gap_pp",
    "addressable_proj_3y_usd",
    "addressable_proj_5y_usd",
    "peer_best_share_pct",
    "peer_top_exporter",
    "num_suppliers_latest",
    "buyer_herfindahl_index",
    "lane_volatility_cv",
    "lane_max_drawdown_pct",
    "signal_flag",
    "lane_data_years",
    "lane_last_year",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exporter", default="CHN", help="Exporter ISO3 code")
    parser.add_argument("--limit", type=int, default=50, help="Number of opportunity rows")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "releases" / "pseo-t17-exporter-chn-0001",
    )
    return parser.parse_args()


def normalize_iso3(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z]", "", value).upper()
    if not re.fullmatch(r"[A-Z]{3}", normalized):
        raise SystemExit("--exporter must be a three-letter ISO3 code")
    return normalized


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


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


def query_summary(where: str) -> dict:
    query = (
        f"SELECT count() AS qualifying_opportunities, "
        f"sum(addressable_proj_3y_usd) AS total_addressable_proj_3y_usd, "
        f"sum(addressable_proj_5y_usd) AS total_addressable_proj_5y_usd, "
        f"sum(buyer_imports_latest_usd) AS total_buyer_imports_usd "
        f"FROM {TABLE} WHERE {where} FORMAT JSONEachRow"
    )
    with clickhouse_request(query) as response:
        return json.loads(response.read().decode("utf-8").strip())


def export_rows(where: str, limit: int, destination: Path) -> None:
    columns = ", ".join(OECD_DERIVED_COLUMNS)
    query = (
        f"SELECT {columns} FROM {TABLE} WHERE {where} "
        "ORDER BY coalesce(addressable_proj_3y_usd, 0) DESC, "
        "buyer_imports_latest_usd DESC, importer_iso3 ASC, hs_code ASC "
        f"LIMIT {limit} FORMAT Parquet"
    )
    with clickhouse_request(query) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    exporter = normalize_iso3(args.exporter)
    if not 10 <= args.limit <= 1000:
        raise SystemExit("--limit must be between 10 and 1000")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    where = (
        f"exporter_iso3 = {sql_literal(exporter)} AND importer_iso3 != exporter_iso3 "
        f"AND buyer_imports_latest_usd > {MIN_BUYER_IMPORTS_USD} "
        f"AND lane_data_years >= {MIN_LANE_YEARS}"
    )
    summary = query_summary(where)
    opportunities = args.output_dir / "opportunities.parquet"
    export_rows(where, args.limit, opportunities)
    row_count = parquet.read_metadata(opportunities).num_rows
    if row_count < 10:
        raise SystemExit(f"Expected at least 10 package rows, found {row_count}")

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files = [{"path": opportunities.name, "rows": row_count, "bytes": opportunities.stat().st_size, "sha256": sha256(opportunities)}]
    metadata = {
        "dataset_id": f"pseo-t17-exporter-opportunities-{exporter.lower()}",
        "title": f"Exporter Opportunity Index: {exporter}",
        "template_family": "T17",
        "canonical_key": "TS-EXPORTER-17-OPPORTUNITY-INDEX",
        "grain": "one exporter-importer-HS6 opportunity row",
        "exporter_iso3": exporter,
        "generated_at": generated_at,
        "status": "public-ready-oecd-derived",
        "source_tables": [TABLE],
        "coverage": "eligible opportunity rows through the latest source year",
        "qualification": {
            "buyer_imports_latest_usd_greater_than": MIN_BUYER_IMPORTS_USD,
            "lane_data_years_at_least": MIN_LANE_YEARS,
            "source_qualifying_rows": int(summary.get("qualifying_opportunities") or 0),
            "total_addressable_proj_3y_usd": summary.get("total_addressable_proj_3y_usd"),
            "total_addressable_proj_5y_usd": summary.get("total_addressable_proj_5y_usd"),
            "total_buyer_imports_latest_usd": summary.get("total_buyer_imports_usd"),
        },
        "license": "OECD Terms & Conditions",
        "terms_url": TERMS_URL,
        "source_url": SOURCE_URL,
        "dataflow_url": DATAFLOW_URL,
        "citation": CITATION,
        "acknowledgement": "Source: OECD (2025), Balanced international merchandise trade statistics (BIMTS) - HS2017-6D, OECD Data Explorer.",
        "third_party_context_included": False,
        "excluded_context": ["GDP", "population", "distance", "language", "FTA", "legal system", "religion", "border", "business-entry indicators"],
        "columns": list(OECD_DERIVED_COLUMNS),
        "files": files,
        "data_rows_are_public": True,
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "README.md").write_text(
        f"# Exporter Opportunity Index: {exporter}\n\n"
        "This package contains a ranked sample of product-market opportunities for one exporting country. "
        "Each row represents one exporter, buyer country, and HS6 product combination.\n\n"
        f"- Exporter: `{exporter}`\n"
        f"- Package rows: `{row_count}`\n"
        f"- Source-qualified opportunities: `{metadata['qualification']['source_qualifying_rows']}`\n"
        f"- Grain: `{metadata['grain']}`\n"
        f"- Terms: {TERMS_URL}\n"
        f"- Source: {CITATION} ({SOURCE_URL})\n\n"
        "The rows are ranked by projected addressable trade value and buyer-market demand. "
        "Projected values are estimates, not guaranteed revenue. Calculated fields are derived from reported trade observations. "
        "Macro, tariff, distance, language, and institutional context fields are excluded from this OECD-derived package.\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
