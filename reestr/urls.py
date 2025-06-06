from django.urls import path , include
from . import views
from .views import reestr_list
from .views import add_reestr
from .views import reports_periods
from .views import export_report_excel

urlpatterns = [
    path('', reestr_list, name='reestr_list'),
    path('export/', views.export_excel, name='reestr_export'),
   path('reports/export/', export_report_excel, name='export_report_excel'),
    path('reports/', reports_periods, name='reports_periods'),
    path('add/', add_reestr, name='reestr_add'),  # ← новая страница
    path('sms_blinoff/', include('sms_blinoff.urls')),  
]