#!/usr/bin/env python3
"""Parse Apple Health XML export and extract biometric data."""
import argparse
import json
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from xml.etree.ElementTree import iterparse

METRIC_TYPES = {
    "hrv":     "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
    "rhr":     "HKQuantityTypeIdentifierRestingHeartRate",
    "hr":      "HKQuantityTypeIdentifierHeartRate",
    "spo2":    "HKQuantityTypeIdentifierOxygenSaturation",
    "resp":    "HKQuantityTypeIdentifierRespiratoryRate",
    "energy":  "HKQuantityTypeIdentifierActiveEnergyBurned",
    "sleep":   "HKCategoryTypeIdentifierSleepAnalysis",
    "workout": "HKWorkout",
}

SLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleepDeep": "Deep",
    "HKCategoryValueSleepAnalysisAsleepREM": "REM",
    "HKCategoryValueSleepAnalysisAsleepCore": "Core",
    "HKCategoryValueSleepAnalysisAwake": "Awake",
    "HKCategoryValueSleepAnalysisInBed": "InBed",
    "HKCategoryValueSleepAnalysisAsleep": "Asleep",
    "HKCategoryValueSleepAnalysisAsleepUnspecified": "Asleep",
}

SPO2_FRACTION_TYPES = {"HKQuantityTypeIdentifierOxygenSaturation"}


def parse_date(s):
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def duration_min(start, end):
    if start and end:
        return round((end - start).total_seconds() / 60, 1)
    return 0


def parse_export(path, source_filter, days, type_filter, as_json):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = defaultdict(list)

    target_types = set()
    if type_filter:
        for t in type_filter.split(","):
            t = t.strip().lower()
            if t in METRIC_TYPES:
                target_types.add(METRIC_TYPES[t])
    else:
        target_types = set(METRIC_TYPES.values())

    def open_xml():
        if path.endswith(".zip"):
            z = zipfile.ZipFile(path)
            names = [n for n in z.namelist() if n.endswith(".xml") and "cda" not in n.lower()]
            if not names:
                print("export.xml не найден в ZIP", file=sys.stderr)
                sys.exit(1)
            return z.open(names[0])
        return open(path, "rb")

    with open_xml() as f:
        for event, elem in iterparse(f, events=("end",)):
            tag = elem.tag
            if tag not in ("Record", "Workout"):
                elem.clear()
                continue

            rec_type = elem.get("type") or tag
            if rec_type not in target_types:
                elem.clear()
                continue

            src = elem.get("sourceName", "")
            if source_filter and source_filter.upper() not in src.upper():
                elem.clear()
                continue

            start = parse_date(elem.get("startDate", ""))
            end   = parse_date(elem.get("endDate", ""))
            created = parse_date(elem.get("creationDate", ""))
            ref = start or created
            if ref and ref.tzinfo is None:
                ref = ref.replace(tzinfo=timezone.utc)
            if ref and ref < cutoff:
                elem.clear()
                continue

            if tag == "Workout":
                results["workout"].append({
                    "date": start.strftime("%Y-%m-%d") if start else "?",
                    "activity": elem.get("workoutActivityType", "").replace("HKWorkoutActivityType", ""),
                    "duration_min": duration_min(start, end),
                    "calories": round(float(elem.get("totalEnergyBurned") or 0), 1),
                    "source": src,
                })
            elif rec_type == "HKCategoryTypeIdentifierSleepAnalysis":
                val = SLEEP_VALUES.get(elem.get("value", ""), elem.get("value", ""))
                results["sleep"].append({
                    "date": start.strftime("%Y-%m-%d") if start else "?",
                    "stage": val,
                    "duration_min": duration_min(start, end),
                    "source": src,
                })
            else:
                short = {v: k for k, v in METRIC_TYPES.items()}.get(rec_type, rec_type)
                unit = elem.get("unit", "")
                val = elem.get("value", "")
                try:
                    val = round(float(val), 2)
                    if rec_type in SPO2_FRACTION_TYPES and val <= 1.0:
                        val = round(val * 100, 1)
                except ValueError:
                    pass
                results[short].append({
                    "date": (start or created).strftime("%Y-%m-%d %H:%M") if (start or created) else "?",
                    "value": val,
                    "unit": unit,
                    "source": src,
                })

            elem.clear()

    return dict(results)


def summarize(data):
    lines = []
    for key, records in sorted(data.items()):
        if not records:
            continue
        if key == "sleep":
            by_date = defaultdict(lambda: defaultdict(float))
            for r in records:
                by_date[r["date"]][r["stage"]] += r["duration_min"]
            lines.append(f"\n=== Sleep (by night) ===")
            for date in sorted(by_date)[-7:]:
                stages = by_date[date]
                total = sum(v for k, v in stages.items() if k != "InBed")
                parts = ", ".join(f"{k}: {round(v/60,1)}h" for k, v in sorted(stages.items()) if k not in ("InBed", "Asleep") and v > 0)
                lines.append(f"  {date}: total {round(total/60,1)}h | {parts}")
        elif key == "workout":
            lines.append(f"\n=== Workouts ===")
            for r in sorted(records, key=lambda x: x["date"])[-10:]:
                lines.append(f"  {r['date']}: {r['activity']} {r['duration_min']}min {r['calories']}kcal")
        else:
            vals = [r["value"] for r in records if isinstance(r["value"], (int, float))]
            if vals:
                unit = records[0].get("unit", "")
                lines.append(f"\n=== {key.upper()} ({unit}) — last {len(vals)} readings ===")
                lines.append(f"  Latest : {vals[-1]} ({records[-1]['date']})")
                lines.append(f"  7d avg : {round(sum(vals)/len(vals), 1)}")
                lines.append(f"  7d min : {min(vals)}  max: {max(vals)}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to export.zip or export.xml")
    ap.add_argument("--source", default="WHOOP", help="Filter by source name (default: WHOOP, use '' for all)")
    ap.add_argument("--days", type=int, default=7, help="Last N days (default: 7)")
    ap.add_argument("--type", dest="type_filter", default="", help="Comma-separated: hrv,rhr,sleep,workout,spo2,resp")
    ap.add_argument("--json", action="store_true", help="Output raw JSON")
    args = ap.parse_args()

    print(f"Парсинг {args.path} | source={args.source or 'all'} | days={args.days}...", file=sys.stderr)
    data = parse_export(args.path, args.source, args.days, args.type_filter, args.json)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        summary = summarize(data)
        if summary.strip():
            print(summary)
        else:
            print(f"Данных не найдено для source='{args.source}' за последние {args.days} дней.")
            print("Попробуй: --source '' для всех источников, или --days 30 для более широкого диапазона.")


if __name__ == "__main__":
    main()
