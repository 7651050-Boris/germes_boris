#!/usr/bin/env python3
"""Fetch wagon specs from vagon.by and create reference table in wagons.db."""

import sqlite3, json, re, time, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DB_PATH = "/Users/boris_ai/.hermes/profiles/boris/data/wagons.db"
SPECS_URL = "https://vagon.by/model/{}"

def get_top_models(limit=80):
    """Get models ranked by count from DB."""
    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    rows = db.execute(
        "SELECT model, COUNT(*) FROM wagons "
        "WHERE model != '' AND model IS NOT NULL AND model != '000000000000' "
        "GROUP BY model ORDER BY 2 DESC LIMIT ?", (limit,)
    ).fetchall()
    db.close()
    return [r[0] for r in rows]

def fetch_specs(model):
    """Fetch specs page for a model and extract structured data."""
    import urllib.parse

    # URL-encode in case of Cyrillic model names
    url = SPECS_URL.format(urllib.parse.quote(model))
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; WagonBot/1.0)"})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as e:
        print(f"  [{model}] HTTP error: {e}")
        return None

    spec = {"model": model}

    # Extract key-value pairs from HTML tables and definition lists
    # Pattern: <td>Key</td><td>Value</td> or Key: Value
    
    # Extract all table rows
    rows = re.findall(r'<tr>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*</tr>', html)
    
    field_map = {
        "Модель:": None,
        "Наименование:": "type_name",
        "Тип вагона:": "type_desc",
        "Завод-изготовитель:": "factory",
        "Тележка:": "bogie",
        "Осность вагона:": "axles",
        "Конструкционная скорость:": "speed",
        "Тара вагона (минимальная):": "tare_min",
        "Тара вагона (максимальная):": "tare_max",
        "Грузоподъёмность:": "capacity",
        "Объём:": "volume",
        "Максимальная расчетная статическая нагрузка от колесной пары на рельсы:": "axle_load",
        "Максимальная расчетная погонная нагрузка:": "linear_load",
        "База вагона:": "wheelbase",
        "Ширина колеи:": "gauge",
        "Год начала серийного производства:": "production_start",
        "Нормативный срок службы:": "service_life_years",
        "Габарит по ГОСТ 9238-2013:": "gabarit",
        "Материал кузова:": "body_material",
        "Наличие переходной площадки:": "has_bridge",
    }

    for key, val in rows:
        key_clean = key.strip()
        val_clean = val.strip()
        # Clean HTML entities
        val_clean = val_clean.replace("&nbsp;", " ").replace("&laquo;", "«").replace("&raquo;", "»")
        if key_clean in field_map and field_map[key_clean]:
            spec[field_map[key_clean]] = val_clean

    # Extract numeric values
    for field in ["tare_min", "tare_max", "capacity", "volume"]:
        if field in spec:
            m = re.search(r'(\d+\.?\d*)', str(spec[field]))
            spec[field] = float(m.group(1)) if m else None

    # Axle load — extract kN value
    if "axle_load" in spec:
        m = re.search(r'(\d+\.?\d*)', str(spec["axle_load"]))
        spec["axle_load_kn"] = float(m.group(1)) if m else None
        # Convert kN to tons: divide by 9.81
        if spec["axle_load_kn"]:
            spec["axle_load_ton"] = round(spec["axle_load_kn"] / 9.81, 1)
        del spec["axle_load"]  # Don't try to insert this

    # Rename fields to match DB columns
    if "gauge" in spec:
        spec["gauge_mm"] = spec.pop("gauge")
    if "speed" in spec:
        spec["speed_kmh"] = spec.pop("speed")
    if "wheelbase" in spec:
        spec["wheelbase_mm"] = spec.pop("wheelbase")
    if "service_life_years" in spec:
        pass  # already has correct name

    # Axles
    if "axles" in spec:
        m = re.search(r'(\d+)', str(spec["axles"]))
        spec["axles"] = int(m.group(1)) if m else None

    # Speed
    if "speed" in spec:
        m = re.search(r'(\d+)', str(spec["speed"]))
        spec["speed_kmh"] = int(m.group(1)) if m else None

    # Service life
    if "service_life_years" in spec:
        m = re.search(r'(\d+)', str(spec["service_life_years"]))
        spec["service_life_years"] = int(m.group(1)) if m else None

    # Wheelbase
    if "wheelbase" in spec:
        m = re.search(r'(\d+)', str(spec["wheelbase"]))
        spec["wheelbase_mm"] = int(m.group(1)) if m else None

    # Gauge
    if "gauge" in spec:
        m = re.search(r'(\d+)', str(spec["gauge"]))
        spec["gauge_mm"] = int(m.group(1)) if m else None

    return spec

def create_specs_table():
    """Create wagon_specs table if not exists."""
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS wagon_specs (
            model TEXT PRIMARY KEY,
            type_name TEXT,
            type_desc TEXT,
            factory TEXT,
            bogie TEXT,
            axles INTEGER,
            tare_min REAL,
            tare_max REAL,
            capacity REAL,
            volume REAL,
            axle_load_kn REAL,
            axle_load_ton REAL,
            linear_load TEXT,
            wheelbase_mm INTEGER,
            gauge_mm INTEGER,
            speed_kmh INTEGER,
            production_start INTEGER,
            service_life_years INTEGER,
            gabarit TEXT,
            body_material TEXT,
            has_bridge TEXT
        )
    """)
    db.commit()
    db.close()

def main():
    models = get_top_models(80)
    print(f"Fetching specs for {len(models)} models...")

    create_specs_table()
    db = sqlite3.connect(DB_PATH)

    success = 0
    for i, model in enumerate(models):
        print(f"[{i+1}/{len(models)}] {model}...", end=" ", flush=True)
        spec = fetch_specs(model)
        
        if spec and len(spec) > 2:  # At least model + some data
            # Only insert columns that exist in wagon_specs table
            existing_cols = {r[1] for r in db.execute("PRAGMA table_info(wagon_specs)").fetchall()}
            valid_spec = {k: v for k, v in spec.items() if k in existing_cols}
            
            if len(valid_spec) > 1:  # At least model + 1 other field
                columns = list(valid_spec.keys())
                placeholders = ", ".join(["?" for _ in columns])
                cols_str = ", ".join(columns)
                values = [valid_spec[c] for c in columns]
                
                try:
                    db.execute(
                        f"INSERT OR REPLACE INTO wagon_specs ({cols_str}) VALUES ({placeholders})",
                        values
                    )
                    db.commit()
                    fields = [k for k in valid_spec if k != "model" and valid_spec[k] is not None]
                    print(f"✓ ({len(fields)} fields)")
                    success += 1
                except Exception as e:
                    print(f"✗ DB error: {e}")
            else:
                print("✗ (no matching columns)")
        else:
            print("✗ (no data)")

        time.sleep(0.3)  # Be polite to the server

    db.close()
    print(f"\nDone: {success}/{len(models)} models with specs")

    # Show summary
    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    count = db.execute("SELECT COUNT(*) FROM wagon_specs").fetchone()[0]
    axles = db.execute("SELECT axles, COUNT(*) FROM wagon_specs GROUP BY axles ORDER BY 1").fetchall()
    print(f"\nTotal specs in DB: {count}")
    for a, c in axles:
        print(f"  {a}-axle: {c} models")

    # Axle load range
    al = db.execute(
        "SELECT MIN(axle_load_ton), MAX(axle_load_ton), AVG(axle_load_ton) FROM wagon_specs WHERE axle_load_ton IS NOT NULL"
    ).fetchone()
    if al and al[0]:
        print(f"  Axle load range: {al[0]:.1f} – {al[1]:.1f} t/axle (avg {al[2]:.1f})")

    db.close()

if __name__ == "__main__":
    main()
