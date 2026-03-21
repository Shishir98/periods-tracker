from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.journal_list,   name='journal_list'),
    path('new/',                    views.journal_entry,  name='journal_new'),
    path('<str:entry_date>/',       views.journal_entry,  name='journal_entry'),
    path('delete/<int:pk>/',        views.journal_delete, name='journal_delete'),
]