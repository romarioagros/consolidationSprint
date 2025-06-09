from django.urls import path
from . import views

app_name = 'sms_blinoff'   # пространство имён для именованных URL этой аппки

urlpatterns = [
    path('tranks/', views.company_list, name='company_list'),
    path("companies/add/", views.add_company, name="add_account"),
    path("mother/add/", views.add_mother, name="add_mother"),
    path("mother/", views.mother_list, name="mother_list"),
]