from django.shortcuts import render
from django.db import connections
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings


def rtu19SrcDays(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
    print(f"Запрос отчета1: {start_date} → {end_date}")  # <-- добавляем лог  
    # если пользователь не указал, взять сегодня как start и end
    from datetime import date
    today_str = date.today().isoformat()
    if not start_date:
        start_date = today_str
    if not end_date:
        end_date = today_str
    print(f"Запрос отчета: {start_date} → {end_date}")  # <-- добавляем лог    

    # загружаем SQL
    sql_path = os.path.join(settings.BASE_DIR, 'voice', 'sql', 'rtu19SrcDays.sql')
    with open(sql_path, 'r', encoding='utf-8') as f:
        query = f.read()

    # выполнение запроса
    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute(query, {'start_date': start_date, 'end_date': end_date})
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
    # print(f"Найдено строк: {len(rows)}")  # <-- добавляем лог    

    return render(request, 'voice/rtu19SrcDays.html', {
        'rows': rows,
        'start_date': start_date,
        'end_date': end_date,
     
    })
