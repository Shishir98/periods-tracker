from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.manage_habits, name='manage_habits'),
    path('log/<str:entry_date>/',   views.log_habits,    name='log_habits'),
    path('edit/<int:pk>/',          views.edit_habit,    name='edit_habit'),
    path('delete/<int:pk>/',        views.delete_habit,  name='delete_habit'),
    path('history/',                views.habit_history, name='habit_history'),
]