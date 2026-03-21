from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('log/', views.log_entry, name='log_entry'),
    path('log/<str:entry_date>/', views.log_entry, name='log_entry_date'),
    path('delete/<int:pk>/', views.delete_entry, name='delete_entry'),
    path('history/', views.history, name='history'),

]
