from django.views import View
from django.shortcuts import render
from django.db import connections
from django.conf import settings
from datetime import date
import os


class SQLReportView(View):
    sql_filename = None
    template_name = 'voice/rtuDays.html'
    connection_name = 'pg_consolidation'
    HeadOfTable = 'отчет по голосу Rtu -19 для Src'
    NameTab = 'Src Name'

    def get_dates(self, request):
        today_str = date.today().isoformat()
        start_date = request.GET.get('start_date') or request.POST.get('start_date') or today_str
        end_date = request.GET.get('end_date') or request.POST.get('end_date') or today_str
        return start_date, end_date

    def get_sql_path(self):
        if not self.sql_filename or not self.sql_filename.endswith('.sql'):
            raise ValueError("Invalid SQL filename")
        return os.path.join(settings.BASE_DIR, 'voice', 'sql', self.sql_filename)

    def get(self, request):
        return self.render_report(request)

    def post(self, request):
        return self.render_report(request)

    def render_report(self, request):
        start_date, end_date = self.get_dates(request)
        sql_path = self.get_sql_path()

        if not os.path.exists(sql_path):
            return render(request, 'error.html', {'message': f'Файл {self.sql_filename} не найден'})

        with open(sql_path, 'r', encoding='utf-8') as f:
            query = f.read()

        with connections[self.connection_name].cursor() as cursor:
            cursor.execute(query, {'start_date': start_date, 'end_date': end_date})
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return render(request, self.template_name, {
            'rows': rows,
            'start_date': start_date,
            'end_date': end_date,
            'sql_filename': self.sql_filename,
            'NameOfTable' : self.HeadOfTable,
            'NameTab' :self.NameTab,
        })


class Rtu19SrcDaysView(SQLReportView):
    sql_filename = 'rtu19SrcDays.sql'
   

class Rtu19DstDaysView(SQLReportView):
    sql_filename = 'rtu19DstDays.sql'
    HeadOfTable = 'отчет по голосу Rtu -19 для Dst'
    NameTab = 'Dst Name'

class Rtu26SrcDaysView(SQLReportView):
    sql_filename = 'rtu26SrcDays.sql'
    HeadOfTable = 'отчет по голосу Rtu -26 для SRC'
    NameTab = 'SRC Name'
    
class Rtu26DstDaysView(SQLReportView):
    sql_filename = 'rtu26DstDays.sql'
    HeadOfTable = 'отчет по голосу Rtu -26 для Dst'
    NameTab = 'Dst Name'    
    

class RtuNew1SrcDaysView(SQLReportView):
    sql_filename = 'rtuNew1SrcDays.sql'
    HeadOfTable = 'отчет по голосу Rtu NEW 1 для Src'
    NameTab = 'Src Name'  


class RtuNew1DstDaysView(SQLReportView):
    sql_filename = 'rtuNew1DstDays.sql'
    HeadOfTable = 'отчет по голосу Rtu NEW 1 для Dst'
    NameTab = 'Dst Name'   


class RtuNew2SrcDaysView(SQLReportView):
    sql_filename = 'rtuNew2SrcDays.sql'
    HeadOfTable = 'отчет по голосу Rtu NEW 2 для Src'
    NameTab = 'Src Name'  


class RtuNew2DstDaysView(SQLReportView):
    sql_filename = 'rtuNew2DstDays.sql'
    HeadOfTable = 'отчет по голосу Rtu NEW 2 для Dst'
    NameTab = 'Dst Name'   


class RtuCbSrcDaysView(SQLReportView):
    sql_filename = 'rtuСbSrcDays.sql'
    HeadOfTable = 'отчет по голосу Rtu CB для Src'
    NameTab = 'Src Name'  


class RtuDstDaysView(SQLReportView):
    sql_filename = 'rtuСbDstDays.sql'
    HeadOfTable = 'отчет по голосу Rtu CB для Dst'
    NameTab = 'Dst Name'    



