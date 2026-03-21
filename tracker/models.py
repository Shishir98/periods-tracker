from django.db import models


class CycleEntry(models.Model):
    FLOW_CHOICES = [
        ('spotting', 'Spotting'),
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('heavy', 'Heavy'),
    ]

    MOOD_CHOICES = [
        ('calm', 'Calm'),
        ('anxious', 'Anxious'),
        ('irritable', 'Irritable'),
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('fatigued', 'Fatigued'),
        ('energized', 'Energized'),
    ]

    date = models.DateField(unique=True)
    is_period_day = models.BooleanField(default=True)
    flow = models.CharField(max_length=20, choices=FLOW_CHOICES, blank=True, null=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True, null=True)
    cramps = models.BooleanField(default=False)
    headache = models.BooleanField(default=False)
    bloating = models.BooleanField(default=False)
    fatigue = models.BooleanField(default=False)
    protected_sex = models.BooleanField(default=False)
    unprotected_sex = models.BooleanField(default=False)
    oral_contraception = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Entry for {self.date}"
