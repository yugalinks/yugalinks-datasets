#!/usr/bin/env python3
"""Build a ranked cross-mart lane catalog and Parquet sample from ClickHouse."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as parquet


DATABASE = "trade_gold_oecd_bimts_6d"
OPPORTUNITY = f"{DATABASE}.msme__serve__opportunity"
RISK_LANE = f"{DATABASE}.risk__lane_monitor_all__20260713"
IMPORT_MARKET = f"{DATABASE}.product__import_market_all__20260715"
EXPORTER_POSITION = f"{DATABASE}.product__exporter_all__20260715"
PRICE_RANKING = f"{DATABASE}.oecd_bimts_6d__price__market_ranking__20260710"
CORRIDOR_RISK = f"{DATABASE}.risk__corridor_monitor_all__20260713"
TOP_CORRIDOR = f"{DATABASE}.product__top_corridor_all__20260715"
PRODUCT_OVERVIEW = f"{DATABASE}.product__overview_all__20260715"
COUNTRY_PROFILE = f"{DATABASE}.gold__country_profile_enriched__20260708"
COUNTRY_RISK = f"{DATABASE}.risk__country_monitor_all__20260713"
CORRIDOR_INTELLIGENCE = f"{DATABASE}.gold__corridor_intelligence_real__20260709"

BASE_COLUMNS = (
    "exporter_iso3",
    "importer_iso3",
    "hs_code",
    "hs_description",
    "buyer_imports_latest_usd",
    "buyer_cagr_full_pct",
    "buyer_yoy_latest_pct",
    "buyer_imports_proj_3y_usd",
    "exports_latest_usd",
    "share_latest_pct",
    "cagr_full_pct",
    "addressable_proj_3y_usd",
    "addressable_proj_5y_usd",
    "your_share_gap_pp",
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

BASE_TABLES = [OPPORTUNITY]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=25000)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "releases" / "top-25000-cross-mart",
    )
    return parser.parse_args()


def clickhouse_url() -> str:
    host = os.getenv("CLICKHOUSE_HOST") or os.getenv("CLICKHOUSE_VM_HOST") or "127.0.0.1"
    if host == "host.docker.internal":
        host = "127.0.0.1"
    return f"http://{host}:{os.getenv('CLICKHOUSE_PORT', '8123')}/"


def query_rows(sql: str, timeout: int = 300) -> list[dict]:
    headers: dict[str, str] = {"content-type": "text/plain; charset=utf-8"}
    user = os.getenv("CLICKHOUSE_USER")
    if user:
        headers["X-ClickHouse-User"] = user
        headers["X-ClickHouse-Key"] = os.getenv("CLICKHOUSE_PASSWORD", "")
    query_params = urllib.parse.urlencode({"max_query_size": "4000000", "max_threads": "4"})
    request = urllib.request.Request(
        f"{clickhouse_url()}?{query_params}",
        data=(sql.rstrip() + " FORMAT JSONEachRow").encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return [
                json.loads(line)
                for line in response.read().decode("utf-8").splitlines()
                if line.strip()
            ]
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"ClickHouse query failed ({error.code}): {detail}") from error


def sql_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def tuple_filter(keys: list[tuple[str, ...]], columns: tuple[str, ...]) -> str:
    if not keys:
        return "(1 = 0)"
    values = ",".join("(" + ",".join(sql_literal(value) for value in key) + ")" for key in keys)
    return f"({','.join(columns)}) IN ({values})"


def key(row: dict, *columns: str) -> tuple[str, ...]:
    return tuple(str(row.get(column) or "") for column in columns)


def value(row: dict, name: str):
    return row.get(name)


def numeric(value_):
    if value_ is None or value_ == "":
        return None
    try:
        result = float(value_)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def source_inventory() -> list[dict]:
    return query_rows(
        "SELECT name, engine FROM system.tables "
        "WHERE database = 'trade_gold_oecd_bimts_6d' ORDER BY name"
    )


def get_base_rows(limit: int) -> list[dict]:
    ranked_rows = query_rows(
        f"SELECT exporter_iso3, importer_iso3, hs_code, addressable_proj_3y_usd, "
        f"buyer_imports_latest_usd FROM {OPPORTUNITY} "
        "WHERE buyer_imports_latest_usd > 50000 "
        "AND lane_data_years >= 3 "
        "AND addressable_proj_3y_usd > 0 "
        "ORDER BY addressable_proj_3y_usd DESC, buyer_imports_latest_usd DESC, "
        "exporter_iso3 ASC, importer_iso3 ASC, hs_code ASC "
        f"LIMIT {limit}"
    )
    lane_keys = [key(row, "exporter_iso3", "importer_iso3", "hs_code") for row in ranked_rows]
    details = query_rows(
        f"SELECT {', '.join(BASE_COLUMNS)} FROM {OPPORTUNITY} WHERE "
        + tuple_filter(lane_keys, ("exporter_iso3", "importer_iso3", "hs_code"))
    )
    detail_map = {key(row, "exporter_iso3", "importer_iso3", "hs_code"): row for row in details}
    missing = [lane_key for lane_key in lane_keys if lane_key not in detail_map]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} ranked opportunity rows during detail fetch")
    return [detail_map[lane_key] for lane_key in lane_keys]


def fetch_lookups(rows: list[dict]) -> dict[str, dict]:
    lane_keys = [key(row, "exporter_iso3", "importer_iso3", "hs_code") for row in rows]
    pair_keys = [key(row, "exporter_iso3", "importer_iso3") for row in rows]
    exporter_product_keys = [key(row, "exporter_iso3", "hs_code") for row in rows]
    importer_product_keys = [key(row, "importer_iso3", "hs_code") for row in rows]
    product_keys = [key(row, "hs_code") for row in rows]
    exporters = sorted({row[0] for row in pair_keys})

    lookups: dict[str, dict] = {}

    risk_rows = query_rows(
        f"SELECT exporter_iso3, importer_iso3, hs_code, attention_level AS risk_attention_level, "
        f"primary_risk_reason, risk_driver_count, volatility_label, drawdown_label, "
        f"competition_label, demand_label FROM {RISK_LANE} WHERE "
        + tuple_filter(lane_keys, ("exporter_iso3", "importer_iso3", "hs_code"))
    )
    lookups["risk"] = {key(row, "exporter_iso3", "importer_iso3", "hs_code"): row for row in risk_rows}

    import_rows = query_rows(
        f"SELECT importer_iso3, hs_code, demand_momentum_label, trend_label, market_hhi_latest, "
        f"supplier_count_latest, coverage_score, confidence_label FROM {IMPORT_MARKET} WHERE "
        + tuple_filter(importer_product_keys, ("importer_iso3", "hs_code"))
    )
    lookups["import_market"] = {key(row, "importer_iso3", "hs_code"): row for row in import_rows}

    exporter_rows = query_rows(
        f"SELECT exporter_iso3, hs_code, active_market_count, trend_label AS exporter_trend_label, "
        f"destination_hhi, weighted_volatility_cv, coverage_score AS exporter_coverage_score, "
        f"confidence_label AS exporter_confidence_label FROM {EXPORTER_POSITION} WHERE "
        + tuple_filter(exporter_product_keys, ("exporter_iso3", "hs_code"))
    )
    lookups["exporter_position"] = {key(row, "exporter_iso3", "hs_code"): row for row in exporter_rows}

    price_rows = query_rows(
        f"SELECT exporter_iso3, hs_code, num_markets, highest_price_importer_iso3, "
        f"highest_price_usd_per_ton, lowest_price_importer_iso3, lowest_price_usd_per_ton, "
        f"median_price_across_markets, price_spread_pct, total_trade_value_usd FROM {PRICE_RANKING} WHERE "
        + tuple_filter(exporter_product_keys, ("exporter_iso3", "hs_code"))
    )
    lookups["price"] = {key(row, "exporter_iso3", "hs_code"): row for row in price_rows}

    corridor_rows = query_rows(
        f"SELECT exporter_iso3, importer_iso3, attention_level AS corridor_attention_level, "
        f"primary_risk_reason AS corridor_primary_risk_reason, current_product_count, "
        f"trade_weighted_volatility_cv FROM {CORRIDOR_RISK} WHERE "
        + tuple_filter(pair_keys, ("exporter_iso3", "importer_iso3"))
    )
    lookups["corridor_risk"] = {key(row, "exporter_iso3", "importer_iso3"): row for row in corridor_rows}

    top_corridor_rows = query_rows(
        f"SELECT exporter_iso3, importer_iso3, hs_code, corridor_rank, attention_level AS "
        f"corridor_attention_level, signal_flag AS corridor_signal_flag FROM {TOP_CORRIDOR} WHERE "
        + tuple_filter(lane_keys, ("exporter_iso3", "importer_iso3", "hs_code"))
    )
    lookups["top_corridor"] = {key(row, "exporter_iso3", "importer_iso3", "hs_code"): row for row in top_corridor_rows}

    product_rows = query_rows(
        f"SELECT hs_code FROM {PRODUCT_OVERVIEW} WHERE "
        + tuple_filter(product_keys, ("hs_code",))
    )
    lookups["product"] = {key(row, "hs_code"): row for row in product_rows}

    exporter_list = ",".join(sql_literal(code) for code in exporters)
    profile_rows = query_rows(
        f"SELECT country_iso3, year, momentum_score, risk_score, exports_usd, imports_usd "
        f"FROM {COUNTRY_PROFILE} WHERE country_iso3 IN ({exporter_list}) "
        "ORDER BY year DESC LIMIT 1 BY country_iso3"
    )
    lookups["country_profile"] = {key(row, "country_iso3"): row for row in profile_rows}

    country_risk_rows = query_rows(
        f"SELECT country_iso3, attention_level AS country_attention_level, "
        f"primary_risk_driver FROM {COUNTRY_RISK} WHERE country_iso3 IN ({exporter_list})"
    )
    lookups["country_risk"] = {key(row, "country_iso3"): row for row in country_risk_rows}

    signal_rows = query_rows(
        f"SELECT exporter_iso3, importer_iso3, hs_code, "
        f"countIf(new_corridor_signal_type = 'new') AS new_signal_count, "
        f"countIf(anomaly_type != '') AS anomaly_count FROM {CORRIDOR_INTELLIGENCE} "
        "PREWHERE year = 2024 AND "
        + tuple_filter(lane_keys, ("exporter_iso3", "importer_iso3", "hs_code"))
        + " GROUP BY exporter_iso3, importer_iso3, hs_code"
    )
    lookups["signals"] = {key(row, "exporter_iso3", "importer_iso3", "hs_code"): row for row in signal_rows}
    return lookups


def enrich_rows(base_rows: list[dict], lookups: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    entries: list[dict] = []
    flat_rows: list[dict] = []
    for rank, base in enumerate(base_rows, start=1):
        exporter = str(base["exporter_iso3"])
        importer = str(base["importer_iso3"])
        hs_code = str(base["hs_code"])
        lane_key = (exporter, importer, hs_code)
        pair_key = (exporter, importer)
        exporter_product_key = (exporter, hs_code)
        importer_product_key = (importer, hs_code)
        product_key = (hs_code,)
        matches = {
            "opportunity": base,
            "risk": lookups["risk"].get(lane_key),
            "import_market": lookups["import_market"].get(importer_product_key),
            "exporter_position": lookups["exporter_position"].get(exporter_product_key),
            "price": lookups["price"].get(exporter_product_key),
            "corridor_risk": lookups["corridor_risk"].get(pair_key),
            "top_corridor": lookups["top_corridor"].get(lane_key),
            "product": lookups["product"].get(product_key),
            "country_profile": lookups["country_profile"].get((exporter,)),
            "country_risk": lookups["country_risk"].get((exporter,)),
            "signals": lookups["signals"].get(lane_key),
        }
        algorithms = [name for name, match in matches.items() if match is not None]
        dataset_id = f"cross-mart-lane-{rank:05d}-{exporter.lower()}-{importer.lower()}-{hs_code}"
        description = base.get("hs_description") or f"HS6 product {hs_code}"
        source_tables = [
            OPPORTUNITY,
            *([RISK_LANE] if matches["risk"] else []),
            *([IMPORT_MARKET] if matches["import_market"] else []),
            *([EXPORTER_POSITION] if matches["exporter_position"] else []),
            *([PRICE_RANKING] if matches["price"] else []),
            *([CORRIDOR_RISK] if matches["corridor_risk"] else []),
            *([TOP_CORRIDOR] if matches["top_corridor"] else []),
            *([PRODUCT_OVERVIEW] if matches["product"] else []),
            *([COUNTRY_PROFILE] if matches["country_profile"] else []),
            *([COUNTRY_RISK] if matches["country_risk"] else []),
            *([CORRIDOR_INTELLIGENCE] if matches["signals"] else []),
        ]
        entry = {
            "dataset_id": dataset_id,
            "title": f"Cross-mart trade lane dossier: {description} from {exporter} to {importer}",
            "kind": "cross-mart-trade-lane",
            "grain": "exporter_iso3 x importer_iso3 x hs_code",
            "filters": {"exporter_iso3": exporter, "importer_iso3": importer, "hs_code": hs_code},
            "algorithms": algorithms,
            "algorithm_count": len(algorithms),
            "source_tables": source_tables,
            "source_coverage": "1995-2024",
            "preview": {"rows": 1, "url": f"/datasets/{dataset_id}/preview"},
            "download": {"mode": "cross-mart-filtered", "url": f"/datasets/{dataset_id}/download", "collection": "top-25000-cross-mart"},
            "rank": rank,
            "latest_year": int(base["lane_last_year"]),
            "history_years": int(base["lane_data_years"]),
            "estimated_addressable_3y_usd": numeric(base.get("addressable_proj_3y_usd")),
        }
        entries.append(entry)

        risk = matches["risk"] or {}
        market = matches["import_market"] or {}
        exporter_position = matches["exporter_position"] or {}
        price = matches["price"] or {}
        corridor = matches["corridor_risk"] or {}
        top_corridor = matches["top_corridor"] or {}
        country_profile = matches["country_profile"] or {}
        country_risk = matches["country_risk"] or {}
        signals = matches["signals"] or {}
        flat_rows.append({
            "rank": rank,
            "dataset_id": dataset_id,
            "exporter_iso3": exporter,
            "importer_iso3": importer,
            "hs_code": hs_code,
            "hs_description": description,
            "buyer_imports_latest_usd": numeric(base.get("buyer_imports_latest_usd")),
            "buyer_cagr_full_pct": numeric(base.get("buyer_cagr_full_pct")),
            "buyer_yoy_latest_pct": numeric(base.get("buyer_yoy_latest_pct")),
            "buyer_imports_proj_3y_usd": numeric(base.get("buyer_imports_proj_3y_usd")),
            "exports_latest_usd": numeric(base.get("exports_latest_usd")),
            "share_latest_pct": numeric(base.get("share_latest_pct")),
            "cagr_full_pct": numeric(base.get("cagr_full_pct")),
            "addressable_proj_3y_usd": numeric(base.get("addressable_proj_3y_usd")),
            "addressable_proj_5y_usd": numeric(base.get("addressable_proj_5y_usd")),
            "your_share_gap_pp": numeric(base.get("your_share_gap_pp")),
            "peer_best_share_pct": numeric(base.get("peer_best_share_pct")),
            "peer_top_exporter": base.get("peer_top_exporter"),
            "num_suppliers_latest": base.get("num_suppliers_latest"),
            "buyer_herfindahl_index": numeric(base.get("buyer_herfindahl_index")),
            "lane_volatility_cv": numeric(base.get("lane_volatility_cv")),
            "lane_max_drawdown_pct": numeric(base.get("lane_max_drawdown_pct")),
            "signal_flag": base.get("signal_flag"),
            "lane_data_years": base.get("lane_data_years"),
            "lane_last_year": base.get("lane_last_year"),
            "opportunity_attention_level": None,
            "opportunity_primary_risk_reason": None,
            "risk_attention_level": risk.get("risk_attention_level"),
            "risk_primary_reason": risk.get("primary_risk_reason"),
            "risk_driver_count": risk.get("risk_driver_count"),
            "volatility_label": risk.get("volatility_label"),
            "drawdown_label": risk.get("drawdown_label"),
            "competition_label": risk.get("competition_label"),
            "demand_label": risk.get("demand_label"),
            "demand_momentum_label": market.get("demand_momentum_label"),
            "market_trend_label": market.get("trend_label"),
            "market_hhi_latest": numeric(market.get("market_hhi_latest")),
            "market_supplier_count_latest": market.get("supplier_count_latest"),
            "market_coverage_score": numeric(market.get("coverage_score")),
            "exporter_active_market_count": exporter_position.get("active_market_count"),
            "exporter_trend_label": exporter_position.get("exporter_trend_label"),
            "exporter_destination_hhi": numeric(exporter_position.get("destination_hhi")),
            "exporter_volatility_cv": numeric(exporter_position.get("weighted_volatility_cv")),
            "price_market_count": price.get("num_markets"),
            "highest_price_importer_iso3": price.get("highest_price_importer_iso3"),
            "highest_price_usd_per_ton": numeric(price.get("highest_price_usd_per_ton")),
            "lowest_price_importer_iso3": price.get("lowest_price_importer_iso3"),
            "lowest_price_usd_per_ton": numeric(price.get("lowest_price_usd_per_ton")),
            "median_price_across_markets": numeric(price.get("median_price_across_markets")),
            "price_spread_pct": numeric(price.get("price_spread_pct")),
            "corridor_attention_level": corridor.get("corridor_attention_level"),
            "corridor_primary_risk_reason": corridor.get("corridor_primary_risk_reason"),
            "corridor_current_product_count": corridor.get("current_product_count"),
            "corridor_volatility_cv": numeric(corridor.get("trade_weighted_volatility_cv")),
            "top_corridor_rank": top_corridor.get("corridor_rank"),
            "top_corridor_attention_level": top_corridor.get("corridor_attention_level"),
            "top_corridor_signal_flag": top_corridor.get("corridor_signal_flag"),
            "country_momentum_score": numeric(country_profile.get("momentum_score")),
            "country_risk_score": numeric(country_profile.get("risk_score")),
            "country_profile_year": country_profile.get("year"),
            "country_attention_level": country_risk.get("country_attention_level"),
            "country_primary_risk_driver": country_risk.get("primary_risk_driver"),
            "new_signal_count_2024": signals.get("new_signal_count", 0),
            "anomaly_count_2024": signals.get("anomaly_count", 0),
            "algorithm_count": len(algorithms),
            "algorithms": ",".join(algorithms),
        })
    return entries, flat_rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    if not 100 <= args.limit <= 25000:
        raise SystemExit("--limit must be between 100 and 25000")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = source_inventory()
    base_rows = get_base_rows(args.limit)
    if len(base_rows) != args.limit:
        raise SystemExit(f"Expected {args.limit} base candidates, found {len(base_rows)}")
    lookups = fetch_lookups(base_rows)
    entries, flat_rows = enrich_rows(base_rows, lookups)
    parquet_path = output_dir / "cross_mart_lane_catalog.parquet"
    catalog_path = output_dir / "catalog.jsonl"
    manifest_path = output_dir / "manifest.json"
    parquet.write_table(pa.Table.from_pylist(flat_rows), parquet_path, compression="zstd")
    with catalog_path.open("w", encoding="utf-8") as stream:
        for entry in entries:
            stream.write(json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n")

    coverage_counts: dict[str, int] = {}
    for entry in entries:
        for algorithm in entry["algorithms"]:
            coverage_counts[algorithm] = coverage_counts.get(algorithm, 0) + 1
    algorithm_count_values = [entry["algorithm_count"] for entry in entries]
    manifest = {
        "catalog_name": "Yugalinks Top Cross-Mart Trade Lane Catalog",
        "status": "local-preview-not-published",
        "requested_dataset_count": args.limit,
        "logical_dataset_count": len(entries),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "ranking": {
            "base_table": OPPORTUNITY,
            "filters": ["buyer_imports_latest_usd > 50000", "lane_data_years >= 3", "addressable_proj_3y_usd > 0"],
            "order": ["addressable_proj_3y_usd DESC", "buyer_imports_latest_usd DESC", "exporter_iso3", "importer_iso3", "hs_code"],
        },
        "source_inventory": {
            "database": DATABASE,
            "objects": len(inventory),
            "physical_tables": sum(row["engine"] != "View" for row in inventory),
            "views": sum(row["engine"] == "View" for row in inventory),
            "names": [row["name"] for row in inventory],
        },
        "algorithm_coverage": {
            "minimum_algorithms_per_dataset": min(algorithm_count_values),
            "maximum_algorithms_per_dataset": max(algorithm_count_values),
            "average_algorithms_per_dataset": round(sum(algorithm_count_values) / len(algorithm_count_values), 2),
            "datasets_by_algorithm": coverage_counts,
        },
        "files": {
            "catalog": {"path": catalog_path.name, "bytes": catalog_path.stat().st_size, "sha256": sha256(catalog_path)},
            "parquet": {"path": parquet_path.name, "rows": len(flat_rows), "bytes": parquet_path.stat().st_size, "sha256": sha256(parquet_path)},
        },
        "data_rows_exported": True,
        "note": "This is one cross-mart Parquet collection plus 25,000 logical entries, not 25,000 separate platform listings.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Top Cross-Mart Trade Lane Catalog\n\n"
        "This local preview contains 25,000 ranked exporter-importer-HS6 lane records. "
        "Each Parquet row combines the opportunity ranking with matching risk, demand, exporter, price, corridor, product, country, and 2024 signal indicators where available.\n\n"
        "- The entries are ranked by projected three-year addressable trade value, then buyer-market demand.\n"
        "- The source inventory contains 43 physical gold tables and one compatibility view.\n"
        "- This is one grouped Parquet collection plus a 25,000-entry catalog, not 25,000 separate platform uploads.\n"
        "- The catalog is local and not published until it is reviewed.\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
