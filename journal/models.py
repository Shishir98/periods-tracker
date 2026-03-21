from django.db import models

# Create your models here.
from django.db import models


class JournalEntry(models.Model):
    date       = models.DateField(unique=True)
    title      = models.CharField(max_length=200, blank=True, default='')
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Journal — {self.date}"

    def excerpt(self):
        return self.content[:120] + '…' if len(self.content) > 120 else self.content