from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, datetime
from .models import JournalEntry


def journal_list(request):
    entries = JournalEntry.objects.all()
    return render(request, 'journal/list.html', {'entries': entries})


def journal_entry(request, entry_date=None):
    instance     = None
    initial_date = date.today()

    if entry_date:
        try:
            d = datetime.strptime(entry_date, '%Y-%m-%d').date()
        except ValueError:
            return redirect('journal_list')
        initial_date = d
        instance = JournalEntry.objects.filter(date=d).first()

    if request.method == 'POST':
        d_str   = request.POST.get('date', '')
        try:
            d = datetime.strptime(d_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            d = initial_date
        title   = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if content:
            if instance:
                instance.title   = title
                instance.content = content
                instance.date    = d
                instance.save()
            else:
                JournalEntry.objects.update_or_create(
                    date=d,
                    defaults={'title': title, 'content': content}
                )
            messages.success(request, 'Entry saved.')
        return redirect('journal_list')

    return render(request, 'journal/entry.html', {
        'instance':     instance,
        'initial_date': initial_date,
    })


def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Entry deleted.')
    return redirect('journal_list')