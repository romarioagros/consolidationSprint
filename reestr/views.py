from django.shortcuts import render
from .models import Reestr
import pandas as pd
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connections
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt  # временно, если нет CSRF token
from django.utils import timezone
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages




def load_sql(file_name):
    path = os.path.join(settings.BASE_DIR, 'reestr', 'sql', file_name)
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()




def reestr_list(request):
    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute('''
            SELECT 
               id, service_id, revenue_type, contractor, contract_number,
                sign_date, subject, code, type, status
            FROM agrements.reestr
            
        ''')
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'reestr_list.html', {'reestr': rows})


def export_excel(request):
    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute('''
            SELECT 
               id, service_id, revenue_type, contractor, contract_number,
               sign_date, subject, code, type, status
            FROM agrements.reestr
        ''')
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=columns)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="reestr.xlsx"'
    df.to_excel(response, index=False)
    return response


def index(request):
    return render(request, 'index.html')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
def add_reestr(request):

    
    if request.method == 'POST':
        data = request.POST

        # Получение IP-адреса пользователя
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Получение текущего времени
        created_at = timezone.now()

        try:
            with connections['pg_consolidation'].cursor() as cursor:
                cursor.execute('''
                    INSERT INTO agrements.reestr (
                        service_id, revenue_type, contractor, contract_number,
                        sign_date, subject, code, type, status, created_at, creator_ip
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', [
                    data.get('service_id'),
                    data.get('revenue_type'),
                    data.get('contractor'),
                    data.get('contract_number'),
                    data.get('sign_date'),
                    data.get('subject'),
                    data.get('code'),
                    data.get('type'),
                    data.get('status'),
                    created_at,
                    ip
                ])
            return redirect('reestr_list')
        except Exception as e:
            # Обработка ошибки вставки
            return HttpResponse(f"Ошибка при добавлении записи: {e}", status=500)

    return render(request, 'reestr_add.html')

    # views.py



    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute("SELECT DISTINCT period_name FROM agrements.periods ORDER BY period_name DESC")
        periods = [row[0] for row in cursor.fetchall()]

    parsed = []
    month_map = {
        "January": "Январь", "February": "Февраль", "March": "Март",
        "April": "Апрель", "May": "Май", "June": "Июнь",
        "July": "Июль", "August": "Август", "September": "Сентябрь",
        "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"
    }

    for p in periods:
        if "_" in p:
            month_eng, year = p.split("_")
            parsed.append({
                'month': month_map.get(month_eng, month_eng),
                'year': year,
                'raw': p
            })

    return render(request, 'period_select.html', {'periods': parsed})

def parse_period_name(month, year):
    eng_months = {
        'Январь': 'January', 'Февраль': 'February', 'Март': 'March',
        'Апрель': 'April', 'Май': 'May', 'Июнь': 'June',
        'Июль': 'July', 'Август': 'August', 'Сентябрь': 'September',
        'Октябрь': 'October', 'Ноябрь': 'November', 'Декабрь': 'December'
    }
    return f"{eng_months.get(month, month)}_{year}"

@csrf_exempt
def reports_periods(request):
    context = {}
    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute("SELECT period_name FROM agrements.periods")
        periods = cursor.fetchall()

    # Разбиваем period_name на месяц и год
    months, years = set(), set()
    for (name,) in periods:
        try:
            month, year = name.split("_")
            months.add(month)
            years.add(year)
        except ValueError:
            continue

    context['months'] = sorted(months)
    context['years'] = sorted(years, reverse=True)
    context['report_data'] = None

    if request.method == "POST":
        selected_month = request.POST.get("month")
        selected_year = request.POST.get("year")
        context['selected_month'] = selected_month
        context['selected_year'] = selected_year
        period_name = f"{selected_month}_{selected_year}"
        query = load_sql('report_query.sql')
        with connections['pg_consolidation'].cursor() as cursor:
            cursor.execute(query, {'period_name': period_name})
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            context['report_data'] = [dict(zip(columns, row)) for row in rows]

    return render(request, 'period_select.html', context)



def export_report_excel(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    if not month or not year:
        return HttpResponse("Missing month or year", status=400)

    period_name = f"{month}_{year}"

    query = load_sql('report_query.sql')
    with connections['pg_consolidation'].cursor() as cursor:
            cursor.execute(query, {'period_name': period_name})
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

    df = pd.DataFrame(rows, columns=columns)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="report_{period_name}.xlsx"'
    df.to_excel(response, index=False)
    return response 





