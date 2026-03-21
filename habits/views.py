import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, datetime, timedelta
from .models import Habit, HabitLog


def _build_month_grid(habits, year, month):
    _, days_in_month = calendar.monthrange(year, month)
    days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    grid = {}
    for habit in habits:
        logs = HabitLog.objects.filter(habit=habit, date__in=days)
        grid[habit.id] = {log.date: log.status for log in logs}
    return days, grid


def manage_habits(request):
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        emoji = request.POST.get('emoji', '●').strip() or '●'
        color = request.POST.get('color', '#c26a4a').strip()
        if name:
            Habit.objects.create(name=name, emoji=emoji, color=color)
            messages.success(request, f'Habit "{name}" added.')
        return redirect('manage_habits')

    today  = date.today()
    year   = int(request.GET.get('year',  today.year))
    month  = int(request.GET.get('month', today.month))
    if month < 1:  month = 12; year -= 1
    if month > 12: month = 1;  year += 1

    habits     = Habit.objects.all()
    active     = habits.filter(is_active=True)
    days, grid = _build_month_grid(active, year, month)

    prev_month = month - 1 or 12
    prev_year  = year - (1 if month == 1 else 0)
    next_month = month % 12 + 1
    next_year  = year + (1 if month == 12 else 0)

    return render(request, 'habits/manage.html', {
        'habits':      habits,
        'active':      active,
        'days':        days,
        'grid':        grid,
        'today':       today,
        'year':        year,
        'month':       month,
        'month_name':  date(year, month, 1).strftime('%B %Y').lower(),
        'prev_year':   prev_year,  'prev_month': prev_month,
        'next_year':   next_year,  'next_month': next_month,
    })


def edit_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk)
    if request.method == 'POST':
        habit.name      = request.POST.get('name', habit.name).strip() or habit.name
        habit.emoji     = request.POST.get('emoji', habit.emoji).strip() or habit.emoji
        habit.color     = request.POST.get('color', habit.color).strip()
        habit.is_active = 'is_active' in request.POST
        habit.save()
        messages.success(request, 'Habit updated.')
        return redirect('manage_habits')
    return render(request, 'habits/edit_habit.html', {'habit': habit})


def delete_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk)
    if request.method == 'POST':
        habit.delete()
        messages.success(request, 'Habit removed.')
    return redirect('manage_habits')


def log_habits(request, entry_date):
    try:
        d = datetime.strptime(entry_date, '%Y-%m-%d').date()
    except ValueError:
        return redirect('dashboard')

    habits = Habit.objects.filter(is_active=True)

    if request.method == 'POST':
        for habit in habits:
            status = request.POST.get(f'status_{habit.id}')
            notes  = request.POST.get(f'notes_{habit.id}', '')
            if status in ('done', 'partial', 'not_done'):
                HabitLog.objects.update_or_create(
                    habit=habit, date=d,
                    defaults={'status': status, 'notes': notes}
                )
        messages.success(request, 'Habits logged.')
        return redirect('dashboard')

    existing   = {log.habit_id: log for log in HabitLog.objects.filter(date=d)}
    habit_data = [{'habit': h, 'log': existing.get(h.id)} for h in habits]

    return render(request, 'habits/log.html', {
        'habit_data': habit_data,
        'entry_date': d,
    })