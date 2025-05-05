"""
URL configuration for reestrAgrement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path ,include
from reestr.views import index
from reestr.views import reports_periods
from reestr.views import export_report_excel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('reports/',reports_periods,name='reports_periods'),
    path('reports/export/', export_report_excel, name='export_report_excel'),
     path('reestr/', include('reestr.urls'))
]
