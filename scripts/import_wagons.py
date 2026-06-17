#!/usr/bin/env python3
"""Import XLSB wagon data → SQLite using python-calamine (Rust, fast)"""
import sqlite3, sys
from pathlib import Path
from python_calamine import load_workbook

XLSB_PATH = "/tmp/wagons.xlsb"
DB_PATH = Path.home() / ".hermes/profiles/boris/data/wagons.db"

HEADERS_EN = [
    "wagon_num", "wagon_type", "wagon_subtype", "specialization",
    "build_date", "model", "ownership", "fleet", "fleet_type",
    "fleet_state", "in_vm", "malfunction_flag", "lease_flag",
    "accounting", "owner", "state_owner", "lessee", "egrpo_owner",
    "operator", "station", "railway", "service_interval",
    "last_depot_repair", "next_repair", "last_overhaul",
    "last_current1", "last_current2", "overhaul_depot",
    "overhaul_date", "overhaul_extension", "empty_mileage",
    "total_mileage", "build_year", "service_life", "factory",
    "depot", "modernization_code", "modernization_date",
    "main_modernization", "main_modernization_date", "wagon_cond_type",
    "extension_end_date", "service_expired", "standard_term",
    "extended_term"
]


def main():
    print(f"Loading {XLSB_PATH}...")
    wb = load_workbook(XLSB_PATH)

    # Create DB
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=OFF")
    db.execute("PRAGMA cache_size=-512000")

    cols_def = ",\n    ".join(f'"{h}" TEXT' for h in HEADERS_EN)
    db.execute(f'CREATE TABLE wagons (\n    {cols_def}\n)')
    placeholders = ','.join(['?'] * len(HEADERS_EN))

    total_rows = 0
    BATCH = 20000

    for sheet_name in wb.sheet_names:
        print(f"Reading {sheet_name}...")
        sheet = wb.get_sheet_by_name(sheet_name)
        rows = sheet.to_python()
        print(f"  {len(rows):,} total rows in sheet")

        batch = []
        data_count = 0

        for i, row in enumerate(rows):
            if i == 0:
                continue  # skip header

            # Skip completely empty rows
            if all(v is None or v == '' for v in row):
                continue

            data_count += 1
            vals = []
            for j in range(len(HEADERS_EN)):
                if j < len(row):
                    v = row[j]
                    vals.append(str(v) if v not in (None, '') else None)
                else:
                    vals.append(None)

            batch.append(vals)

            if len(batch) >= BATCH:
                db.executemany(f'INSERT INTO wagons VALUES ({placeholders})', batch)
                db.commit()
                total_rows += len(batch)
                print(f"  {total_rows:,} data rows imported", end='\r')
                batch = []

        if batch:
            db.executemany(f'INSERT INTO wagons VALUES ({placeholders})', batch)
            db.commit()
            total_rows += len(batch)

        print(f"  {sheet_name}: {data_count:,} data rows (skipped {len(rows)-1-data_count:,} empty)")

    print(f"\nTotal data rows: {total_rows:,}")

    # Indexes
    print("\nCreating indexes...")
    idx_cols = ["wagon_num", "wagon_type", "ownership", "owner", "railway",
                "fleet", "fleet_state", "fleet_type"]
    for col in idx_cols:
        try:
            db.execute(f'CREATE INDEX idx_{col} ON wagons("{col}")')
            db.commit()
            print(f"  ✓ {col}")
        except Exception as e:
            print(f"  ✗ {col}: {e}")

    print("\nAnalyzing...")
    db.execute("ANALYZE")
    db.commit()
    db.close()

    size_mb = DB_PATH.stat().st_size / 1024 / 1024
    print(f"\n✅ Done! {DB_PATH} ({size_mb:.0f} MB)")


if __name__ == "__main__":
    main()
