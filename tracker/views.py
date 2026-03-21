from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, timedelta
import json

from .models import CycleEntry
from .forms import CycleEntryForm


def _get_late_info(stats, logged_dates, today):
    """Check if period is late and return overdue dates for calendar marking."""
    predicted = stats['next_predicted']
    avg_cycle = stats['avg_cycle']
    avg_period = stats['avg_period']
    last_start = stats['last_start']

    cycle_day = (today - last_start).days + 1 if last_start else None
    cycle_normal = 27 <= avg_cycle <= 32

    if not predicted:
        return {
            'is_late': False, 'days_late': 0,
            'cycle_day': cycle_day, 'cycle_normal': cycle_normal,
            'overdue_dates': []
        }

    days_late = (today - predicted).days  # negative = not due yet

    # Only flag as late if 2+ days past predicted start and no period logged since
    recent_period = any(
        d >= str(predicted) for d in logged_dates
    )
    is_late = days_late >= 2 and not recent_period

    # Build list of overdue dates: from predicted_start up to today (if late)
    overdue_dates = []
    if is_late:
        for i in range(avg_period):
            d = predicted + timedelta(days=i)
            if d <= today and str(d) not in logged_dates:
                overdue_dates.append(str(d))

    return {
        'is_late': is_late,
        'days_late': days_late if is_late else 0,
        'cycle_day': cycle_day,
        'cycle_normal': cycle_normal,
        'overdue_dates': overdue_dates,
    }


def _get_cycle_stats(entries):
    period_days = sorted([e.date for e in entries if e.is_period_day])
    if not period_days:
        return {'avg_cycle': 28, 'avg_period': 5, 'last_start': None, 'next_predicted': None}

    cycles = []
    current = [period_days[0]]
    for d in period_days[1:]:
        if (d - current[-1]).days <= 2:
            current.append(d)
        else:
            cycles.append(current)
            current = [d]
    cycles.append(current)

    # Ignore single isolated days — must be 2+ consecutive days to count as a real period
    cycles = [c for c in cycles if len(c) >= 2]

    avg_period = round(sum(len(c) for c in cycles) / len(cycles)) if len(cycles) >= 3 else 5

    starts = [c[0] for c in cycles]
    if len(starts) >= 2:
        lengths = [(starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)]
        avg_cycle = round(sum(lengths) / len(lengths))
    else:
        avg_cycle = 28

    last_start = starts[-1] if starts else None
    next_predicted = last_start + timedelta(days=avg_cycle) if last_start else None

    return {
        'avg_cycle': avg_cycle,
        'avg_period': avg_period,
        'last_start': last_start,
        'next_predicted': next_predicted,
    }


def _get_phase_dates(stats, from_date, num_cycles=3):
    """
    Return {date_str: phase} only for dates >= from_date (today).
    Ovulation window is 5 days centred on cycle_length - 14.
    """
    last_start = stats['last_start']
    if not last_start:
        return {}

    avg_cycle = stats['avg_cycle']
    avg_period = stats['avg_period']
    ovulation_day = avg_cycle - 14

    phase_map = {}
    for offset in range(-1, num_cycles + 1):
        cycle_start = last_start + timedelta(days=avg_cycle * offset)
        for day_num in range(avg_cycle):
            d = cycle_start + timedelta(days=day_num)
            if d < from_date:
                continue
            ds = str(d)
            if day_num < avg_period:
                phase_map[ds] = 'menstrual'
            elif day_num < ovulation_day - 2:
                phase_map[ds] = 'follicular'
            elif day_num <= ovulation_day + 2:
                phase_map[ds] = 'ovulation'
            else:
                phase_map[ds] = 'luteal'
    return phase_map


def dashboard(request):
    today   = date.today()
    entries = CycleEntry.objects.all()
    stats   = _get_cycle_stats(entries)

    logged_dates = set(str(e.date) for e in entries if e.is_period_day)
    sex_dates    = set(str(e.date) for e in entries if e.protected_sex or e.unprotected_sex)

    phase_dates = _get_phase_dates(stats, from_date=today, num_cycles=13)
    for d in logged_dates:
        phase_dates.pop(d, None)

    late_info = _get_late_info(stats, logged_dates, today)
    for d in late_info['overdue_dates']:
        phase_dates.pop(d, None)

    days_since = None
    if stats['last_start']:
        days_since = (today - stats['last_start']).days

    days_until = None
    if stats['next_predicted']:
        days_until = (stats['next_predicted'] - today).days

    recent      = entries[:5]
    habit_stats = _get_habit_stats(today)

    try:
        from journal.models import JournalEntry
        journal_dates = set(str(e.date) for e in JournalEntry.objects.all())
    except ImportError:
        journal_dates = set()

    try:
        from habits.models import HabitLog
        habit_logged_dates = set(
            str(d) for d in HabitLog.objects.values_list('date', flat=True).distinct()
        )
    except ImportError:
        habit_logged_dates = set()

    context = {
        'today':               today,
        'stats':               stats,
        'logged_dates_json':   json.dumps(list(logged_dates)),
        'sex_dates_json':      json.dumps(list(sex_dates)),
        'phase_dates_json':    json.dumps(phase_dates),
        'overdue_dates_json':  json.dumps(late_info['overdue_dates']),
        'journal_dates_json':  json.dumps(list(journal_dates)),
        'habit_dates_json':    json.dumps(list(habit_logged_dates)),
        'late_info':           late_info,
        'days_since':          days_since,
        'days_until':          days_until,
        'recent':              recent,
        'total_entries':       entries.count(),
        'habit_stats':         habit_stats,
    }
    return render(request, 'tracker/dashboard.html', context)

def log_entry(request, entry_date=None):
    initial = {}
    instance = None

    if entry_date:
        try:
            from datetime import datetime
            d = datetime.strptime(entry_date, '%Y-%m-%d').date()
        except ValueError:
            return redirect('dashboard')
        try:
            instance = CycleEntry.objects.get(date=d)
        except CycleEntry.DoesNotExist:
            initial['date'] = d
    else:
        initial['date'] = date.today()

    if request.method == 'POST':
        form = CycleEntryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entry saved.')
            return redirect('dashboard')
    else:
        form = CycleEntryForm(instance=instance, initial=initial)

    return render(request, 'tracker/log_entry.html', {'form': form, 'instance': instance})


def delete_entry(request, pk):
    entry = get_object_or_404(CycleEntry, pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Entry removed.')
    return redirect('dashboard')


def history(request):
    entries = CycleEntry.objects.all()
    stats = _get_cycle_stats(entries)
    return render(request, 'tracker/history.html', {'entries': entries, 'stats': stats})


def _get_habit_stats(today):
    try:
        from habits.models import Habit, HabitLog
    except ImportError:
        return []

    habits = Habit.objects.filter(is_active=True)
    if not habits.exists():
        return []

    import calendar
    result      = []
    month_start = today.replace(day=1)
    days_so_far = today.day  # how many days have passed this month

    for habit in habits:
        # Streak
        streak = 0
        d = today
        while streak < 365:
            log = HabitLog.objects.filter(habit=habit, date=d).first()
            if log and log.status in ('done', 'partial'):
                streak += 1
                d -= timedelta(days=1)
            else:
                break

        # Monthly completion % (out of days elapsed this month)
        month_logs = HabitLog.objects.filter(
            habit=habit,
            date__gte=month_start,
            date__lte=today
        )
        done_count = month_logs.filter(status__in=('done', 'partial')).count()
        month_pct  = round((done_count / days_so_far) * 100) if days_so_far else 0

        today_log = HabitLog.objects.filter(habit=habit, date=today).first()

        result.append({
            'habit':        habit,
            'streak':       streak,
            'month_pct':    month_pct,
            'done_count':   done_count,
            'days_so_far':  days_so_far,
            'today_status': today_log.status if today_log else None,
        })

    return result