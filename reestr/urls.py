from django.urls import path
from . import views
from .views import reestr_list
from .views import add_reestr

urlpatterns = [
    path('', reestr_list, name='reestr_list'),
    path('export/', views.export_excel, name='reestr_export'),
    path('add/', add_reestr, name='reestr_add'),  # ← новая страница
]