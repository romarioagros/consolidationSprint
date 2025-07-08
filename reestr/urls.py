# reestr/urls.py
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('',                    login_required(views.reestr_list),    name='reestr_list'),
    path('add/',                login_required(views.add_reestr),     name='reestr_add'),
    path('export/',             login_required(views.export_excel),   name='reestr_export'),

    # Если нужны отчёты внутри модуля:
    path('reports/',            login_required(views.reports_periods),name='reestr_reports'),
    path('reports/export/',     login_required(views.export_report_excel), name='reestr_export_report'),

    # Вложенное приложение sms_blinoff (если у него своя аутентификация, 
    # то там тоже оберните его views в login_required или включите его урлы через middleware)
   
]
