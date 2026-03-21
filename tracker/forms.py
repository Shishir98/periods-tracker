from django import forms
from .models import CycleEntry


class CycleEntryForm(forms.ModelForm):
    class Meta:
        model = CycleEntry
        fields = ['date', 'is_period_day', 'flow', 'mood',
                  'cramps', 'headache', 'bloating', 'fatigue',
                  'protected_sex', 'unprotected_sex', 'oral_contraception',
                  'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'field-input'}),
            'flow': forms.Select(attrs={'class': 'field-input'}),
            'mood': forms.Select(attrs={'class': 'field-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'field-input',
                'rows': 3,
                'placeholder': 'Any notes for today…'
            }),
            'is_period_day':       forms.CheckboxInput(attrs={'class': 'field-check'}),
            'cramps':              forms.CheckboxInput(attrs={'class': 'field-check'}),
            'headache':            forms.CheckboxInput(attrs={'class': 'field-check'}),
            'bloating':            forms.CheckboxInput(attrs={'class': 'field-check'}),
            'fatigue':             forms.CheckboxInput(attrs={'class': 'field-check'}),
            'protected_sex':       forms.CheckboxInput(attrs={'class': 'field-check'}),
            'unprotected_sex':     forms.CheckboxInput(attrs={'class': 'field-check'}),
            'oral_contraception':  forms.CheckboxInput(attrs={'class': 'field-check'}),
        }