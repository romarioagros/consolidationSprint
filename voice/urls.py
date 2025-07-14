from django.urls import path
from . import views

app_name = 'voice'

urlpatterns = [
    path('rtu19SrcDays/', views.rtu19SrcDays, name='rtu19SrcDays'),
    
]