from django.shortcuts import render
from .models import Reestr
import pandas as pd
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connections
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt  # временно, если нет CSRF token
from django.utils import timezone

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