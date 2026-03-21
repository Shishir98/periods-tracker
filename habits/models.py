from django.db import models

# Create your models here.
from django.db import models


class Habit(models.Model):
    name       = models.CharField(max_length=100)
    emoji      = models.CharField(max_length=10, default='✦')
    color      = models.CharField(max_length=7, default='#c26a4a')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.name


class HabitLog(models.Model):
    STATUS_CHOICES = [
        ('done',     'Done'),
        ('partial',  'Partially Done'),
        ('not_done', 'Not Done'),
    ]
    habit      = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date       = models.DateField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_done')
    notes      = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} - {self.date} - {self.status}"