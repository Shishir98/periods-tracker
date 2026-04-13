# Place this file at:
# tracker/management/commands/import_flo_data.py
#
# Run with:
# python manage.py import_flo_data --file /path/to/export.json
# python manage.py import_flo_data --file /path/to/export.json --dry-run

import json
from collections import defaultdict
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from tracker.models import CycleEntry


# --- Mapping helpers ---

INTENSITY_TO_FLOW = {
    1: "light",
    2: "medium",
    3: "heavy",
}

# Maps Flo mood subcategory → CycleEntry.MOOD_CHOICES key
FLO_MOOD_MAP = {
    "Happy":               "happy",
    "Playful":             "happy",
    "Energetic":           "energized",
    "Sad":                 "sad",
    "Depressed":           "sad",
    "Apathetic":           "sad",
    "LowEnergy":           "fatigued",
    "Angry":               "irritable",
    "Swings":              "irritable",
    "VerySelfCritical":    "irritable",
    "Panic":               "anxious",
    "ObsessiveThoughts":   "anxious",
    "Neutral":             "calm",
    "Confused":            "calm",
}

# Symptom subcategories that map to boolean fields on the model
SYMPTOM_MAP = {
    "AbdominalPain": "cramps",
    "DrawingPain":   "cramps",
    "Headache":      "headache",
    "Bloating":      "bloating",
    "Fatigue":       "fatigue",
}


def parse_date(date_str):
    """Parse Flo's date strings like '2021-08-11 00:00:00.0'"""
    return date.fromisoformat(date_str.split(" ")[0])


class Command(BaseCommand):
    help = "Import period tracking data from a Flo JSON export"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Path to the Flo JSON export file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run = options["dry_run"]

        try:
            with open(file_path) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise CommandError(f"Could not load file: {e}")

        op = data.get("operationalData", {})
        cycles = op.get("cycles", [])
        point_events = op.get("point_events_manual_v2", [])

        # --- Step 1: Build a dict of date → entry data from cycles ---
        # Each date in a period range gets is_period_day=True and a flow if available.

        entries = {}  # date → dict of field values

        for cycle in cycles:
            if cycle.get("pregnant"):
                continue  # skip pregnancy cycles

            start_str = cycle.get("period_start_date")
            end_str = cycle.get("period_end_date")
            if not start_str or not end_str:
                continue

            start = parse_date(start_str)
            end = parse_date(end_str)

            # Parse intensity map: {"0": 3, "1": 2, ...} (day offset → intensity level)
            intensity_raw = cycle.get("period_intensity") or "{}"
            try:
                intensity_map = json.loads(intensity_raw) if isinstance(intensity_raw, str) else intensity_raw
            except json.JSONDecodeError:
                intensity_map = {}

            delta = (end - start).days
            for offset in range(delta + 1):
                current_date = start + timedelta(days=offset)
                flow = INTENSITY_TO_FLOW.get(intensity_map.get(str(offset)))
                entries[current_date] = {
                    "is_period_day": True,
                    "flow": flow,
                    "mood": None,
                    "cramps": False,
                    "headache": False,
                    "bloating": False,
                    "fatigue": False,
                    "protected_sex": False,
                    "unprotected_sex": False,
                }

        # --- Step 2: Overlay point events (symptoms, mood, sex) ---
        # Point events can fall on non-period days too, so we create entries for those as well.

        for event in point_events:
            local_date_str = event.get("local_date") or event.get("date")
            if not local_date_str:
                continue

            event_date = parse_date(local_date_str)
            category = event.get("category", "")
            subcategory = event.get("subcategory", "")

            # Ensure an entry exists for this date even if it's not a period day
            if event_date not in entries:
                entries[event_date] = {
                    "is_period_day": False,
                    "flow": None,
                    "mood": None,
                    "cramps": False,
                    "headache": False,
                    "bloating": False,
                    "fatigue": False,
                    "protected_sex": False,
                    "unprotected_sex": False,
                }

            entry = entries[event_date]

            if category == "Mood":
                mapped_mood = FLO_MOOD_MAP.get(subcategory)
                if mapped_mood and entry["mood"] is None:
                    entry["mood"] = mapped_mood

            elif category == "Symptom":
                field = SYMPTOM_MAP.get(subcategory)
                if field:
                    entry[field] = True

            elif category == "Sex":
                if subcategory == "Protected":
                    entry["protected_sex"] = True
                elif subcategory == "Unprotected":
                    entry["unprotected_sex"] = True

        # --- Step 3: Write to database or run EDA ---

        if dry_run:
            self.run_eda(entries, cycles, point_events)
            return

        created = updated = 0
        for entry_date, fields in sorted(entries.items()):
            _, was_created = CycleEntry.objects.update_or_create(
                date=entry_date,
                defaults=fields,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created: {created}, Updated: {updated}"
        ))

    # ---------------------------------------------------------------------------
    # EDA
    # ---------------------------------------------------------------------------

    def run_eda(self, entries, cycles, point_events):
        w = self.stdout.write
        suc = self.style.SUCCESS
        warn = self.style.WARNING

        SEP  = "=" * 60
        SEP2 = "-" * 40

        # ── helpers ──────────────────────────────────────────────────

        def bar(value, total, width=20):
            """Simple ASCII bar: ████░░░░ 3/10"""
            filled = round(width * value / total) if total else 0
            return f"{'█' * filled}{'░' * (width - filled)}  {value}"

        def month_label(year, month):
            return date(year, month, 1).strftime("%b %Y")

        # ── collect period and sex data by date ──────────────────────

        period_dates  = sorted(d for d, e in entries.items() if e["is_period_day"])
        protected_dates   = sorted(d for d, e in entries.items() if e["protected_sex"])
        unprotected_dates = sorted(d for d, e in entries.items() if e["unprotected_sex"])
        any_sex_dates = sorted(set(protected_dates) | set(unprotected_dates))

        # ── 1. OVERVIEW ──────────────────────────────────────────────

        w(f"\n{SEP}")
        w(suc("  DRY RUN — EXPLORATORY DATA ANALYSIS"))
        w(SEP)

        all_dates = sorted(entries.keys())
        w(f"  Data range      : {all_dates[0]}  →  {all_dates[-1]}")
        w(f"  Total entries   : {len(entries)}")
        w(f"  Period days     : {len(period_dates)}")
        w(f"  Sex events      : {len(any_sex_dates)}  "
          f"(protected: {len(protected_dates)}, unprotected: {len(unprotected_dates)})")
        w(f"  Cycles logged   : {len(cycles)}")

        # ── 2. CYCLE LENGTHS ─────────────────────────────────────────

        w(f"\n{SEP2}")
        w("  CYCLE LENGTHS  (gap between period start dates)")
        w(SEP2)

        valid_cycles = [
            c for c in cycles
            if not c.get("pregnant")
            and c.get("period_start_date")
            and c.get("period_end_date")
        ]
        starts = sorted(parse_date(c["period_start_date"]) for c in valid_cycles)
        ends   = {parse_date(c["period_start_date"]): parse_date(c["period_end_date"])
                  for c in valid_cycles}

        cycle_lengths  = [(starts[i+1] - starts[i]).days for i in range(len(starts) - 1)]
        period_lengths = [(ends[s] - s).days + 1 for s in starts if s in ends]

        if cycle_lengths:
            w(f"  Cycle length    : avg {sum(cycle_lengths)/len(cycle_lengths):.1f} days  "
              f"| min {min(cycle_lengths)}  max {max(cycle_lengths)}")
        if period_lengths:
            w(f"  Period length   : avg {sum(period_lengths)/len(period_lengths):.1f} days  "
              f"| min {min(period_lengths)}  max {max(period_lengths)}")

        # ── 3. PERIOD FREQUENCY — MONTHLY ────────────────────────────

        w(f"\n{SEP2}")
        w("  PERIOD DAYS PER MONTH")
        w(SEP2)

        period_by_month = defaultdict(int)
        for d in period_dates:
            period_by_month[(d.year, d.month)] += 1

        max_p = max(period_by_month.values(), default=1)
        for (y, m) in sorted(period_by_month):
            v = period_by_month[(y, m)]
            w(f"  {month_label(y, m):<12}  {bar(v, max_p)}")

        # ── 4. PERIOD FREQUENCY — YEARLY ─────────────────────────────

        w(f"\n{SEP2}")
        w("  PERIOD DAYS PER YEAR")
        w(SEP2)

        period_by_year = defaultdict(int)
        for d in period_dates:
            period_by_year[d.year] += 1

        max_py = max(period_by_year.values(), default=1)
        for y in sorted(period_by_year):
            v = period_by_year[y]
            w(f"  {y}  {bar(v, max_py)}")

        # ── 5. SEX FREQUENCY — MONTHLY ───────────────────────────────

        w(f"\n{SEP2}")
        w("  SEX EVENTS PER MONTH  (P = protected, U = unprotected)")
        w(SEP2)

        sex_by_month_p  = defaultdict(int)
        sex_by_month_u  = defaultdict(int)
        for d in protected_dates:
            sex_by_month_p[(d.year, d.month)] += 1
        for d in unprotected_dates:
            sex_by_month_u[(d.year, d.month)] += 1

        all_sex_months = sorted(set(sex_by_month_p) | set(sex_by_month_u))
        max_s = max(
            [sex_by_month_p[k] + sex_by_month_u[k] for k in all_sex_months],
            default=1
        )
        for (y, m) in all_sex_months:
            p = sex_by_month_p[(y, m)]
            u = sex_by_month_u[(y, m)]
            total = p + u
            w(f"  {month_label(y, m):<12}  {bar(total, max_s)}  (P:{p} U:{u})")

        # ── 6. SEX FREQUENCY — YEARLY ────────────────────────────────

        w(f"\n{SEP2}")
        w("  SEX EVENTS PER YEAR")
        w(SEP2)

        sex_by_year_p = defaultdict(int)
        sex_by_year_u = defaultdict(int)
        for d in protected_dates:
            sex_by_year_p[d.year] += 1
        for d in unprotected_dates:
            sex_by_year_u[d.year] += 1

        all_sex_years = sorted(set(sex_by_year_p) | set(sex_by_year_u))
        max_sy = max(
            [sex_by_year_p[y] + sex_by_year_u[y] for y in all_sex_years],
            default=1
        )
        for y in all_sex_years:
            p = sex_by_year_p[y]
            u = sex_by_year_u[y]
            total = p + u
            w(f"  {y}  {bar(total, max_sy)}  (P:{p} U:{u})")

        # ── 7. SEX vs CYCLE PHASE ─────────────────────────────────────

        w(f"\n{SEP2}")
        w("  SEX TIMING RELATIVE TO PERIOD")
        w(SEP2)

        on_period   = sum(1 for d in any_sex_dates if entries[d]["is_period_day"])
        off_period  = len(any_sex_dates) - on_period
        w(f"  During period   : {on_period}")
        w(f"  Outside period  : {off_period}")

        # Days before next period start
        period_starts_set = set(starts)
        countdown_buckets = defaultdict(int)  # days_before → count
        for d in any_sex_dates:
            upcoming = [s for s in starts if s > d]
            if upcoming:
                days_to_next = (min(upcoming) - d).days
                if days_to_next <= 14:
                    countdown_buckets[days_to_next] += 1

        if countdown_buckets:
            w(f"\n  Sex events in the 14 days before next period:")
            for day in sorted(countdown_buckets):
                label = f"  {day:>2}d before period"
                w(f"  {label}  {bar(countdown_buckets[day], max(countdown_buckets.values()))}")

        # ── 8. PROTECTED vs UNPROTECTED RATIO ────────────────────────

        w(f"\n{SEP2}")
        w("  PROTECTED vs UNPROTECTED RATIO")
        w(SEP2)

        total_sex = len(protected_dates) + len(unprotected_dates)
        if total_sex:
            pct_p = len(protected_dates)   / total_sex * 100
            pct_u = len(unprotected_dates) / total_sex * 100
            w(f"  Protected    {bar(len(protected_dates), total_sex)}  ({pct_p:.0f}%)")
            w(f"  Unprotected  {bar(len(unprotected_dates), total_sex)}  ({pct_u:.0f}%)")

        # ── done ─────────────────────────────────────────────────────

        w(f"\n{SEP}")
        w(warn(f"  Dry run complete — {len(entries)} entries parsed, nothing written."))
        w(SEP + "\n")