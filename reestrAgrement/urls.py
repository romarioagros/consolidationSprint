# reestrAgrement/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from reestr.views import index, reports_periods, export_report_excel

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    # Стандартная auth-логика: login/logout/password-reset и т.д.
    path('accounts/', include('django.contrib.auth.urls')),
    # Главная страница проекта
    path('', login_required(index), name='index'),
    # Если вам нужны «отдельные» урлы для отчетов на уровне проекта
    path('reports/', login_required(reports_periods), name='reports_periods'),
    path('reports/export/', login_required(export_report_excel), name='export_report_excel'),
    # Все урлы приложения reestr (они тоже будут закрыты благодаря декораторам внутри)
    path('reestr/', include('reestr.urls')),
    path('sms_blinoff/',        include('sms_blinoff.urls')),
]
