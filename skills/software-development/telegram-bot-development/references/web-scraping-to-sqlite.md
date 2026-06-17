# Web Scraping to SQLite Reference Tables

Pattern for scraping structured technical data from web sources into SQLite reference tables that can be JOINed with the main data.

## Source: vagon.by

The site `https://vagon.by/model/{model}` provides structured technical specifications for Russian railway wagons. Each page has key-value pairs in HTML tables.

## URL Encoding for Non-ASCII Models

Some model codes contain Cyrillic characters (e.g., `ВПМ-770`, `ПМ-820`). These MUST be URL-encoded:

```python
import urllib.parse
url = f"https://vagon.by/model/{urllib.parse.quote(model)}"
```

Without encoding, `UnicodeEncodeError: 'ascii' codec can't encode characters` will crash the script.

## HTML Parsing Pattern

The pages use simple `<tr><td>Key</td><td>Value</td></tr>` tables:

```python
rows = re.findall(r'<tr>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*</tr>', html)

field_map = {
    "Модель:": None,  # skip — already known
    "Осность вагона:": "axles",
    "Грузоподъёмность:": "capacity",
    "Тара вагона (минимальная):": "tare_min",
    "Тара вагона (максимальная):": "tare_max",
    "Максимальная расчетная статическая нагрузка от колесной пары на рельсы:": "axle_load",
    # ... etc
}
```

## HTML Entity Cleanup

Raw values contain `&nbsp;`, `&laquo;`, `&raquo;` — clean before processing:

```python
val_clean = val_clean.replace("&nbsp;", " ").replace("&laquo;", "«").replace("&raquo;", "»")
```

## Field Name Mapping

The HTML key names don't always match DB column names. Rename after extraction:

```python
if "gauge" in spec:
    spec["gauge_mm"] = spec.pop("gauge")
if "speed" in spec:
    spec["speed_kmh"] = spec.pop("speed")
```

## Safe INSERT — Only Known Columns

Don't assume all extracted fields have matching DB columns. Use PRAGMA:

```python
existing_cols = {r[1] for r in db.execute("PRAGMA table_info(wagon_specs)").fetchall()}
valid_spec = {k: v for k, v in spec.items() if k in existing_cols}

db.execute(
    f"INSERT OR REPLACE INTO table ({','.join(valid_spec)}) VALUES ({','.join(['?']*len(valid_spec))})",
    list(valid_spec.values())
)
```

This prevents `table has no column named X` errors when the parser extracts unexpected fields.

## Rate Limiting

Be polite to the server:

```python
import time
time.sleep(0.3)  # Between requests
```

## Typical Extracted Fields (vagon.by)

| Field | DB Column | Type |
|-------|-----------|------|
| Осность вагона | axles | INTEGER (4/6/8) |
| Грузоподъёмность | capacity | REAL (tons) |
| Тара (мин/макс) | tare_min/max | REAL (tons) |
| Нагрузка на ось | axle_load_kn/ton | REAL (kN / ton-force) |
| Тележка | bogie | TEXT |
| Скорость | speed_kmh | INTEGER |
| Срок службы | service_life_years | INTEGER |
| Завод | factory | TEXT |
| Колея | gauge_mm | INTEGER |

## Axle Load Calculation

The source provides axle load in kN. Convert to ton-force:

```python
axle_load_ton = round(axle_load_kn / 9.81, 1)
```

Typical values: 22.0–25.5 ton-force per axle for modern 4-axle wagons.
