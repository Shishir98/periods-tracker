from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, datetime, timedelta
from .models import Habit, HabitLog


def manage_habits(request):
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        emoji = request.POST.get('emoji', '✦').strip() or '✦'
        color = request.POST.get('color', '#c26a4a').strip()
        if name:
            Habit.objects.create(name=name, emoji=emoji, color=color)
            messages.success(request, f'Habit "{name}" added.')
        return redirect('manage_habits')

    habits = Habit.objects.all()
    return render(request, 'habits/manage.html', {'habits': habits})


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


def habit_history(request):
    habits = Habit.objects.filter(is_active=True)
    today  = date.today()
    days   = [today - timedelta(days=i) for i in range(29, -1, -1)]

    grid = {}
    for habit in habits:
        logs = HabitLog.objects.filter(habit=habit, date__in=days)
        grid[habit.id] = {str(log.date): log.status for log in logs}

    return render(request, 'habits/history.html', {
        'habits': habits,
        'days':   days,
        'grid':   grid,
        'today':  today,
    })