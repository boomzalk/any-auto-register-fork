#!/usr/bin/env python3
"""Standalone exporter for any-auto-register SQLite accounts.

This script does not import the project code. It reads the SQLite database
directly and exports base account columns plus useful fields from `extra_json`.

Examples:
  python export_any_auto_register_accounts.py --db /root/any-auto-register/account_manager.db
  python export_any_auto_register_accounts.py --db /root/any-auto-register/account_manager.db --platform chatgpt --format json
  python export_any_auto_register_accounts.py --db /root/any-auto-register/account_manager.db --platform trae --status registered --output trae.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_FIELDS = [
    "id",
    "platform",
    "email",
    "password",
    "user_id",
    "region",
    "token",
    "status",
    "trial_end_time",
    "cashier_url",
    "created_at",
    "updated_at",
]

EXTRA_FIELDS = [
    "access_token",
    "refresh_token",
    "id_token",
    "session_token",
    "workspace_id",
    "cookies",
    "client_id",
    "account_id",
    "last_refresh",
    "expires_at",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export any-auto-register accounts from account_manager.db."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to SQLite database file, e.g. /root/any-auto-register/account_manager.db",
    )
    parser.add_argument(
        "--platform",
        help="Optional platform filter, e.g. chatgpt, trae, tavily",
    )
    parser.add_argument(
        "--status",
        help="Optional status filter, e.g. registered, invalid, subscribed",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="Export format",
    )
    parser.add_argument(
        "--output",
        help="Output file path. Defaults to accounts_<timestamp>.<ext>",
    )
    return parser.parse_args()


def make_query(platform: str | None, status: str | None) -> tuple[str, list[Any]]:
    sql = "SELECT * FROM accounts"
    clauses = []
    params: list[Any] = []

    if platform:
        clauses.append("platform = ?")
        params.append(platform)
    if status:
        clauses.append("status = ?")
        params.append(status)

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    sql += " ORDER BY id ASC"
    return sql, params


def parse_extra(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def normalize_record(row: sqlite3.Row) -> dict[str, Any]:
    record = {field: row[field] for field in BASE_FIELDS if field in row.keys()}
    extra_raw = row["extra_json"] if "extra_json" in row.keys() else "{}"
    extra = parse_extra(extra_raw)

    for field in EXTRA_FIELDS:
        record[field] = extra.get(field, "")

    record["extra_json"] = extra_raw or "{}"
    return record


def default_output_path(fmt: str, platform: str | None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{platform}_" if platform else ""
    return f"{prefix}accounts_{timestamp}.{fmt}"


def export_csv(records: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = BASE_FIELDS + EXTRA_FIELDS + ["extra_json"]
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def export_json(records: list[dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    output_path = Path(args.output or default_output_path(args.format, args.platform))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        sql, params = make_query(args.platform, args.status)
        rows = conn.execute(sql, params).fetchall()
        records = [normalize_record(row) for row in rows]

        if args.format == "csv":
            export_csv(records, output_path)
        else:
            export_json(records, output_path)
    finally:
        conn.close()

    print(f"Exported {len(records)} accounts to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
