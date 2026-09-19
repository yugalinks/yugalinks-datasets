#!/usr/bin/env python3
"""Build a 50,000-product catalog across the gold mart algorithm families."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as parquet

try:
    from .generate_cross_mart_catalog import key, query_rows, sha256, source_inventory, tuple_filter
except ImportError:
    from generate_cross_mart_catalog import key, query_rows, sha256, source_inventory, tuple_filter


DATABASE = "trade_gold_oecd_bimts_6d"
OUTPUT_DEFAULT = Path(__file__).resolve().parent.parent / "releases" / "top-50000-gold-catalog"

FAMILIES = [
    {
        "family": "opportunity",
        "quota": 15000,
        "table": f"{DATABASE}.msme__serve__opportunity",
        "grain": "exporter_iso3 x importer_iso3 x hs_code",
        "algorithm": "opportunity scoring, addressable market, share gap, and projections",
        "keys": ("exporter_iso3", "importer_iso3", "hs_code"),
        "sql": """
SELECT exporter_iso3, importer_iso3, hs_code, hs_description,
       buyer_imports_latest_usd, buyer_imports_proj_3y_usd,
       exports_latest_usd, share_latest_pct, addressable_proj_3y_usd,
       addressable_proj_5y_usd, your_share_gap_pp, peer_best_share_pct,
       peer_top_exporter, num_suppliers_latest, buyer_herfindahl_index,
       lane_volatility_cv, lane_max_drawdown_pct, signal_flag,
       lane_data_years, lane_last_year
FROM trade_gold_oecd_bimts_6d.msme__serve__opportunity
WHERE buyer_imports_latest_usd > 50000
  AND lane_data_years >= 3
  AND addressable_proj_3y_usd > 0
ORDER BY addressable_proj_3y_usd DESC, buyer_imports_latest_usd DESC,
         exporter_iso3, importer_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "risk_lane",
        "quota": 7500,
        "table": f"{DATABASE}.risk__lane_monitor_all__20260713",
        "grain": "exporter_iso3 x importer_iso3 x hs_code",
        "algorithm": "lane volatility, drawdown, competition, demand, access, and attention labels",
        "keys": ("exporter_iso3", "importer_iso3", "hs_code"),
        "sql": """
SELECT exporter_iso3, importer_iso3, hs_code, hs_description,
       buyer_imports_latest_usd, addressable_proj_3y_usd,
       lane_volatility_cv, lane_max_drawdown_pct, signal_flag,
       lane_data_years, lane_last_year, attention_level,
       primary_risk_reason, risk_driver_count, volatility_label,
       drawdown_label, competition_label, demand_label, access_label,
       risk_driver_labels
FROM trade_gold_oecd_bimts_6d.risk__lane_monitor_all__20260713
WHERE buyer_imports_latest_usd > 50000
  AND lane_data_years >= 3
ORDER BY multiIf(attention_level = 'critical', 4,
                 attention_level = 'high', 3,
                 attention_level = 'watch', 2, 1) DESC,
         addressable_proj_3y_usd DESC, lane_volatility_cv DESC
LIMIT {limit}
""",
    },
    {
        "family": "import_market",
        "quota": 5000,
        "table": f"{DATABASE}.product__import_market_all__20260715",
        "grain": "importer_iso3 x hs_code",
        "algorithm": "buyer demand momentum, supplier count, HHI, and market trend",
        "keys": ("importer_iso3", "hs_code"),
        "sql": """
SELECT importer_iso3, hs_code, first_data_year, latest_data_year,
       years_with_data, imports_latest_observed_usd, imports_avg_3y_usd,
       imports_cagr_3y_pct, latest_vs_all_avg_pct, yoy_growth_latest_pct,
       supplier_count_latest, market_hhi_latest, top_supplier_iso3,
       top_supplier_share_pct, demand_momentum_label, trend_label,
       coverage_score, confidence_label
FROM trade_gold_oecd_bimts_6d.product__import_market_all__20260715
WHERE imports_latest_observed_usd > 50000
  AND years_with_data >= 3
ORDER BY imports_latest_observed_usd DESC, imports_cagr_3y_pct DESC,
         importer_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "price",
        "quota": 5000,
        "table": f"{DATABASE}.oecd_bimts_6d__price__market_ranking__20260710",
        "grain": "exporter_iso3 x hs_code price comparison",
        "algorithm": "highest, lowest, median, and spread of observed market prices",
        "keys": ("exporter_iso3", "hs_code"),
        "sql": """
SELECT exporter_iso3, hs_code, num_markets,
       highest_price_importer_iso3, highest_price_usd_per_ton,
       lowest_price_importer_iso3, lowest_price_usd_per_ton,
       median_price_across_markets, price_spread_pct,
       avg_quantity_metric_tons, total_trade_value_usd
FROM trade_gold_oecd_bimts_6d.oecd_bimts_6d__price__market_ranking__20260710
WHERE num_markets >= 3
ORDER BY price_spread_pct DESC, total_trade_value_usd DESC,
         exporter_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "new_signal",
        "quota": 5000,
        "table": f"{DATABASE}.gold__corridor_intelligence_real__20260709",
        "grain": "exporter_iso3 x importer_iso3 x hs_code x year",
        "algorithm": "new trade corridor signal detection",
        "keys": ("exporter_iso3", "importer_iso3", "hs_code", "year"),
        "sql": """
SELECT year, exporter_iso3, importer_iso3, hs_code,
       market_imports_usd, market_yoy_growth_pct, market_cagr_3y_pct,
       your_market_share_pct, your_share_gap_pp, num_suppliers,
       market_hhi, momentum_yoy_pct, momentum_acceleration_pct,
       new_corridor_signal_type, new_corridor_signal_strength
FROM trade_gold_oecd_bimts_6d.gold__corridor_intelligence_real__20260709
PREWHERE year = 2024
WHERE new_corridor_signal_type = 'new'
ORDER BY new_corridor_signal_strength DESC, market_imports_usd DESC,
         exporter_iso3, importer_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "anomaly",
        "quota": 5000,
        "table": f"{DATABASE}.gold__corridor_intelligence_real__20260709",
        "grain": "exporter_iso3 x importer_iso3 x hs_code x year",
        "algorithm": "trade anomaly type, severity, and z-score detection",
        "keys": ("exporter_iso3", "importer_iso3", "hs_code", "year"),
        "sql": """
SELECT year, exporter_iso3, importer_iso3, hs_code,
       market_imports_usd, market_yoy_growth_pct, market_cagr_3y_pct,
       volatility_cv, max_drawdown_pct, anomaly_type,
       anomaly_severity, anomaly_z_score, num_suppliers, market_hhi
FROM trade_gold_oecd_bimts_6d.gold__corridor_intelligence_real__20260709
PREWHERE year = 2024
WHERE anomaly_type != ''
ORDER BY anomaly_z_score DESC, market_imports_usd DESC,
         exporter_iso3, importer_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "exporter_position",
        "quota": 3000,
        "table": f"{DATABASE}.product__exporter_all__20260715",
        "grain": "exporter_iso3 x hs_code",
        "algorithm": "exporter position, active markets, destination concentration, and trend",
        "keys": ("exporter_iso3", "hs_code"),
        "sql": """
SELECT exporter_iso3, hs_code, first_data_year, latest_data_year,
       observed_lane_count, current_lane_count, active_market_count,
       exports_current_2024_usd, exports_avg_3y_usd, exports_cagr_3y_pct,
       positive_growth_year_share_pct, trend_acceleration_pct,
       trend_label, top_market_iso3, top_market_share_pct,
       destination_hhi, weighted_share_latest_pct,
       weighted_volatility_cv, weighted_max_drawdown_pct,
       coverage_score, confidence_label
FROM trade_gold_oecd_bimts_6d.product__exporter_all__20260715
WHERE exports_current_2024_usd > 50000
  AND active_market_count >= 2
ORDER BY exports_current_2024_usd DESC, active_market_count DESC,
         exporter_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "top_corridor",
        "quota": 2000,
        "table": f"{DATABASE}.product__top_corridor_all__20260715",
        "grain": "exporter_iso3 x importer_iso3 x hs_code",
        "algorithm": "ranked product corridor and market-share context",
        "keys": ("exporter_iso3", "importer_iso3", "hs_code"),
        "sql": """
SELECT exporter_iso3, importer_iso3, hs_code, corridor_rank,
       latest_data_year, lane_data_years, exports_latest_observed_usd,
       buyer_imports_latest_observed_usd, exports_cagr_3y_pct,
       buyer_yoy_latest_pct, market_share_latest_pct,
       peer_best_share_pct, peer_top_exporter, supplier_count_latest,
       buyer_market_hhi, volatility_cv, max_drawdown_pct,
       attention_level, primary_risk_reason, signal_flag, confidence_label
FROM trade_gold_oecd_bimts_6d.product__top_corridor_all__20260715
WHERE corridor_rank <= 25
ORDER BY exports_latest_observed_usd DESC, corridor_rank ASC,
         exporter_iso3, importer_iso3, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "corridor_risk",
        "quota": 1000,
        "table": f"{DATABASE}.risk__corridor_monitor_all__20260713",
        "grain": "exporter_iso3 x importer_iso3 corridor",
        "algorithm": "corridor attention, trade concentration, volatility, and risk drivers",
        "keys": ("exporter_iso3", "importer_iso3"),
        "sql": """
SELECT exporter_iso3, importer_iso3, all_history_lane_count,
       current_lane_count, current_product_count, latest_data_year,
       current_trade_usd, attention_trade_usd, critical_trade_usd,
       critical_lane_count, high_attention_lane_count,
       high_volatility_lane_count, product_concentration_hhi,
       attention_trade_share_pct, critical_trade_share_pct,
       risk_driver_labels, attention_level, primary_risk_reason
FROM trade_gold_oecd_bimts_6d.risk__corridor_monitor_all__20260713
ORDER BY attention_trade_usd DESC, current_trade_usd DESC,
         exporter_iso3, importer_iso3
LIMIT {limit}
""",
    },
    {
        "family": "product_profile",
        "quota": 800,
        "table": f"{DATABASE}.product__overview_all__20260715",
        "grain": "hs_code product profile",
        "algorithm": "product trend, concentration, corridor coverage, and monitored risk",
        "keys": ("hs_code",),
        "sql": """
SELECT hs_code, hs_description, latest_data_year, years_with_data,
       latest_trade_usd, trade_avg_3y_usd, cagr_3y_latest_pct,
       trend_label, exporter_concentration_hhi, importer_concentration_hhi,
       active_importer_count, active_exporter_count, active_corridor_count,
       median_price_across_exporters_usd_per_ton, monitored_risk_lane_count,
       high_attention_lane_count, coverage_score, confidence_label
FROM trade_gold_oecd_bimts_6d.product__overview_all__20260715
ORDER BY latest_trade_usd DESC, active_corridor_count DESC, hs_code
LIMIT {limit}
""",
    },
    {
        "family": "country_profile",
        "quota": 500,
        "table": f"{DATABASE}.gold__country_profile_enriched__20260708",
        "grain": "country_iso3 x year trade profile",
        "algorithm": "country trade, momentum, concentration, macro, and market potential profile",
        "keys": ("country_iso3", "year"),
        "sql": """
SELECT country_iso3, year, exports_usd, imports_usd, trade_balance_usd,
       yoy_exports_growth_pct, exports_cagr_3y_pct, export_partner_hhi,
       export_product_hhi, momentum_score, risk_score, gdp_million_usd,
       gdp_per_capita_usd, population, trade_openness_pct,
       num_active_partners, real_market_potential, foreign_market_potential
FROM trade_gold_oecd_bimts_6d.gold__country_profile_enriched__20260708
ORDER BY year DESC, exports_usd DESC, country_iso3
LIMIT {limit}
""",
    },
    {
        "family": "country_risk",
        "quota": 200,
        "table": f"{DATABASE}.risk__country_monitor_all__20260713",
        "grain": "country_iso3 risk profile",
        "algorithm": "country trade attention, volatility, concentration, and macro resilience",
        "keys": ("country_iso3",),
        "sql": """
SELECT country_iso3, all_history_lane_count, current_lane_count,
       critical_lane_count, high_attention_lane_count,
       high_volatility_lane_count, monitored_exports_current_usd,
       monitored_attention_share_pct, export_weighted_volatility_cv,
       partner_hhi_latest, product_hhi_latest, attention_level,
       primary_risk_driver, macro_resilience_label
FROM trade_gold_oecd_bimts_6d.risk__country_monitor_all__20260713
ORDER BY monitored_attention_share_pct DESC, monitored_exports_current_usd DESC,
         country_iso3
LIMIT {limit}
""",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    return parser.parse_args()


def slug(value: object) -> str:
    return "".join(character.lower() if str(character).isalnum() else "-" for character in str(value)).strip("-")


def title_for(family: dict, row: dict) -> str:
    if "hs_code" in row and "exporter_iso3" in row and "importer_iso3" in row:
        return f"{family['family'].replace('_', ' ').title()}: HS6 {row['hs_code']} from {row['exporter_iso3']} to {row['importer_iso3']}"
    if "hs_code" in row and "importer_iso3" in row:
        return f"{family['family'].replace('_', ' ').title()}: HS6 {row['hs_code']} in {row['importer_iso3']}"
    if "hs_code" in row and "exporter_iso3" in row:
        return f"{family['family'].replace('_', ' ').title()}: HS6 {row['hs_code']} from {row['exporter_iso3']}"
    if "hs_code" in row:
        description = row.get("hs_description") or row["hs_code"]
        return f"{family['family'].replace('_', ' ').title()}: {description}"
    if "country_iso3" in row and "year" in row:
        return f"{family['family'].replace('_', ' ').title()}: {row['country_iso3']} {row['year']}"
    if "country_iso3" in row:
        return f"{family['family'].replace('_', ' ').title()}: {row['country_iso3']}"
    return f"{family['family'].replace('_', ' ').title()} dataset"


def score_for(family: dict, row: dict) -> float | None:
    fields = {
        "opportunity": "addressable_proj_3y_usd",
        "risk_lane": "addressable_proj_3y_usd",
        "import_market": "imports_latest_observed_usd",
        "price": "total_trade_value_usd",
        "new_signal": "market_imports_usd",
        "anomaly": "anomaly_z_score",
        "exporter_position": "exports_current_2024_usd",
        "top_corridor": "exports_latest_observed_usd",
        "corridor_risk": "attention_trade_usd",
        "product_profile": "latest_trade_usd",
        "country_profile": "exports_usd",
        "country_risk": "monitored_attention_share_pct",
    }
    field = fields[family["family"]]
    value = row.get(field)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def fetch_family_rows(family: dict) -> list[dict]:
    template = family["sql"].format(limit=family["quota"])
    select_clause, from_clause = template.split("FROM", 1)
    from_and_where, order_clause = from_clause.split("ORDER BY", 1)
    order_clause = order_clause.split("LIMIT", 1)[0].strip()
    columns = family["keys"]
    ranked = query_rows(
        f"SELECT {', '.join(columns)} FROM {from_and_where} "
        f"ORDER BY {order_clause} LIMIT {family['quota']}"
    )
    ranked_keys = [key(row, *columns) for row in ranked]
    predicate_joiner = " AND " if re.search(r"\bWHERE\b", from_and_where, re.IGNORECASE) else " WHERE "
    details = query_rows(
        f"{select_clause}FROM {from_and_where}{predicate_joiner}"
        + tuple_filter(ranked_keys, columns)
    )
    detail_map = {key(row, *columns): row for row in details}
    missing = [ranked_key for ranked_key in ranked_keys if ranked_key not in detail_map]
    if missing:
        raise RuntimeError(f"{family['family']} lost {len(missing)} rows during detail fetch")
    return [detail_map[ranked_key] for ranked_key in ranked_keys]


def main() -> int:
    args = parse_args()
    if sum(family["quota"] for family in FAMILIES) != 50000:
        raise SystemExit("Family quotas must total exactly 50,000")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    inventory = source_inventory()
    entries: list[dict] = []
    flat_rows: list[dict] = []
    family_counts: dict[str, int] = {}
    global_rank = 0

    for family in FAMILIES:
        rows = fetch_family_rows(family)
        if len(rows) != family["quota"]:
            raise SystemExit(f"{family['family']} returned {len(rows)} rows; expected {family['quota']}")
        family_counts[family["family"]] = len(rows)
        for family_rank, row in enumerate(rows, start=1):
            global_rank += 1
            key_parts = [str(row.get(column, "")) for column in family["keys"]]
            dataset_id = f"gold-{family['family']}-{family_rank:05d}-{'-'.join(slug(part) for part in key_parts)}"
            source_tables = [family["table"]]
            if family["family"] in {"opportunity", "risk_lane"}:
                source_tables.append(f"{DATABASE}.oecd_bimts_6d__core__corridor_product_year__v1")
            entry = {
                "dataset_id": dataset_id,
                "title": title_for(family, row),
                "kind": f"gold-{family['family']}",
                "family": family["family"],
                "grain": family["grain"],
                "filters": {column: row.get(column) for column in family["keys"]},
                "algorithm": family["algorithm"],
                "source_tables": source_tables,
                "source_coverage": "1995-2024",
                "primary_row_count": 1,
                "preview": {"rows": 1, "url": f"/datasets/{dataset_id}/preview"},
                "download": {"mode": "filtered-family-collection", "url": f"/datasets/{dataset_id}/download", "collection": "top-50000-gold-catalog"},
                "rank_within_family": family_rank,
                "rank_global": global_rank,
                "selection_score": score_for(family, row),
            }
            entries.append(entry)
            flat_rows.append({
                "dataset_id": dataset_id,
                "family": family["family"],
                "rank_within_family": family_rank,
                "rank_global": global_rank,
                "title": entry["title"],
                "grain": family["grain"],
                "source_table": family["table"],
                "algorithm": family["algorithm"],
                "filters_json": json.dumps(entry["filters"], ensure_ascii=True, separators=(",", ":")),
                "selection_score": score_for(family, row),
                "primary_payload_json": json.dumps(row, ensure_ascii=True, separators=(",", ":")),
            })

    catalog_path = args.output_dir / "catalog.jsonl"
    parquet_path = args.output_dir / "selected_gold_rows.parquet"
    manifest_path = args.output_dir / "manifest.json"
    with catalog_path.open("w", encoding="utf-8") as output:
        for entry in entries:
            output.write(json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n")
    parquet.write_table(pa.Table.from_pylist(flat_rows), parquet_path, compression="zstd")

    manifest = {
        "catalog_name": "Yugalinks 50,000 Gold Mart Dataset Catalog",
        "status": "local-preview-not-published",
        "logical_dataset_count": len(entries),
        "selected_source_rows": len(flat_rows),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_inventory": {
            "database": DATABASE,
            "objects": len(inventory),
            "physical_tables": sum(row["engine"] != "View" for row in inventory),
            "views": sum(row["engine"] == "View" for row in inventory),
            "names": [row["name"] for row in inventory],
        },
        "family_quotas": family_counts,
        "files": {
            "catalog": {"path": catalog_path.name, "bytes": catalog_path.stat().st_size, "sha256": sha256(catalog_path)},
            "selected_rows": {"path": parquet_path.name, "rows": len(flat_rows), "bytes": parquet_path.stat().st_size, "sha256": sha256(parquet_path)},
        },
        "data_rows_exported": True,
        "note": "This is one grouped selected-row collection plus 50,000 logical entries, not 50,000 separate platform listings.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "README.md").write_text(
        "# 50,000 Gold Mart Dataset Catalog\n\n"
        "This preview contains 50,000 ranked dataset products distributed across the gold mart algorithm families. "
        "The catalog uses all 43 physical gold tables as its source inventory and selects one primary row per product.\n\n"
        "The release is one grouped catalog and Parquet collection, not 50,000 separate platform listings. "
        "Each catalog entry has a stable filter, grain, source table, algorithm description, and download contract.\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
