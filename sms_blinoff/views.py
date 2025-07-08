from django.shortcuts import render
from django.contrib import messages
import datetime
import pandas as pd
from django.http import HttpResponse
from django.http import JsonResponse
from django.db import connections
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt  # временно, если нет CSRF token
from django.utils import timezone
import os
from django.conf import settings
# Create your views here.


def company_list(request):
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute('''
            SELECT C.id, C.name, C.legal_name, C.alians, M.name name_m
	FROM descr.companies C
    left join descr.mother M 
    on C.mother_id = M.id
    order by 1
    ;
            
        ''')
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'company_list.html', {'companies': rows})


def add_company(request):

    """
    Показывает форму создания новой компании (GET) и сохраняет её (POST),
    **но** предполагает, что материнская компания (mother_id) уже есть в descr.mother.
    Чтобы добавить новую мать, нужно сперва перейти на /mother/add/.
    """
    # 1) Загружаем список матерей для SELECT
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name FROM descr.mother ORDER BY name;")
        mothers_raw = cursor.fetchall()
        # Список словарей: [{"id": 1, "name": "Первый"}, {"id": 2, "name": "Второй"}, …]
        mothers = [{"id": m[0], "name": m[1]} for m in mothers_raw]

    if request.method == "POST":
        # 2) Собираем данные из формы
        account_name = request.POST.get("account_name", "").strip()
        legal_name   = request.POST.get("legal_name", "").strip()
        mother_id    = request.POST.get("mother_id", "").strip()
        raw_aliases  = request.POST.getlist("alians")
        aliases      = [a.strip() for a in raw_aliases if a.strip()]

        # 3) Валидация
        error = None
        if not account_name:
            error = "Поле «Название (name)» не может быть пустым."
        elif not legal_name:
            error = "Поле «Юридическое название (legal_name)» не может быть пустым."
        elif not mother_id:
            error = "Нужно выбрать материнскую компанию."
        else:
            try:
                mother_id_int = int(mother_id)
            except (ValueError, TypeError):
                mother_id_int = None

            if mother_id_int is None or not any(m["id"] == mother_id_int for m in mothers):
                error = "Выбранная материнская компания некорректна."

        if not aliases:
            # Дополнительно: потребуем хотя бы один alias
            if error is None:
                error = "Нужно ввести хотя бы один alias."

        if error:
            messages.error(request, error)
            return render(request, "company_add.html", {
                "mothers": mothers,
                "prev_account_name": account_name,
                "prev_legal_name": legal_name,
                "prev_mother_id": mother_id,
                "prev_aliases": aliases,
            })

        # 4) Если всё качественно, вставляем новую компанию:
        #    сначала вычисляем новый ID = max(id)+1
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM descr.companies;")
            max_id = cursor.fetchone()[0] or 0
            new_company_id = max_id + 1

        # 5) Делаем INSERT
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO descr.companies (id, name, legal_name, alians, mother_id)
                VALUES (%s, %s, %s, %s, %s);
            """, [
                new_company_id,
                account_name,
                legal_name,
                aliases,
                mother_id_int
            ])

        messages.success(request, "Новая компания успешно добавлена.")
        # После вставки – перенаправляем пользователя на список компаний
        return redirect("sms_blinoff:company_list")

    # Если GET-запрос, выводим пустую форму
    return render(request, "company_add.html", {
        "mothers": mothers,
        "prev_account_name": "",
        "prev_legal_name": "",
        "prev_mother_id": "",
        "prev_aliases": [],
    })


def add_mother(request):



    """
    Показывает форму для создания новой материнской компании (descr.mother).
    После успешного добавления – редирект на add_account.
    """
    if request.method == "POST":
        mother_name = request.POST.get("mother_name", "").strip()

        if not mother_name:
            messages.error(request, "Поле «Имя материнской компании» не может быть пустым.")
            return render(request, "mother_add.html", {
                "prev_mother_name": ""
            })

        # Вставляем новую материнскую компанию. Используем DEFAULT для ID:
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO descr.mother (name)
                VALUES (%s)
                RETURNING id;
            """, [mother_name])
            new_mother_id = cursor.fetchone()[0]

        messages.success(request, f"Материнская компания «{mother_name}» добавлена (ID={new_mother_id}).")
        # Перенаправляем на форму создания аккаунта
        return redirect("sms_blinoff:add_account")

    # GET-запрос – просто показываем пустую форму
    return render(request, "mother_add.html", {
        "prev_mother_name": ""
    })    


def mother_list(request):
    """
    Показывает все записи из descr.mother и кнопку «Добавить мат.компанию».
    """
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name, creation_date FROM descr.mother ORDER BY  id ;")
        cols = [c[0] for c in cursor.description]
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()]

    return render(request, "mother_list.html", {
        "mothers": rows,
    })

def add_mother(request):
    """
    Форма создания новой материнской компании.
    Параметр GET/POST 'next' определяет, куда вернуть пользователя после сохранения.
    """
    # Откуда пришли. Значение - имя URL из этого же app_name.
    # По умолчанию — назад на add_account.
    next_view = request.GET.get("next") or request.POST.get("next") or "add_account"

    if request.method == "POST":
        mother_name = request.POST.get("mother_name", "").strip()
        if not mother_name:
            messages.error(request, "Поле «Имя материнской компании» не может быть пустым.")
            return render(request, "mother_add.html", {
                "prev_mother_name": "",
                "next": next_view,
            })

        # Вставляем новую мат.компанию
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO descr.mother (name)
                VALUES (%s)
                RETURNING id;
            """, [mother_name])
            new_mother_id = cursor.fetchone()[0]

        messages.success(request, f"Материнская компания «{mother_name}» добавлена (ID={new_mother_id}).")

        # Редирект обратно на нужную view
        return redirect(f"sms_blinoff:{next_view}")

    # GET
    return render(request, "mother_add.html", {
        "prev_mother_name": "",
        "next": next_view,
    })

def alfa_list(request):
    """
    Выдаёт страницу со всеми записями из descr.alfa_numbers_new,
    присоединяя имя матери из descr.mother.
    """
    with connections['pgDataforSMS'].cursor() as c:
        c.execute("""
            SELECT
              AN.id,
              AN.alfa_name,
              M.name       AS mother_name,
              AN.price,
              AN.currency,
              AN.fee,
              AN.data_start,
              AN.data_end,
              AN.data_created
            FROM descr.alfa_numbers_new AN
            LEFT JOIN descr.mother M
              ON AN.id_company = M.id
            ORDER BY AN.id ASC;
        """)
        cols = [col[0] for col in c.description]
        rows = [dict(zip(cols, row)) for row in c.fetchall()]

    return render(request, "alfa_numbers.html", {
        "alfa_list": rows,
    })
def add_alfa(request):
    # 1. Подгружаем список материнских компаний
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name FROM descr.mother ORDER BY name;")
        mothers = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    if request.method == "POST":
        # 2. Читаем форму
        alfa_name   = request.POST.get("alfa_name", "").strip()
        mother_id   = request.POST.get("mother_id", "").strip()
        price       = request.POST.get("price", "").strip()
        currency    = request.POST.get("currency", "").strip()
        fee         = request.POST.get("fee", "").strip()
        data_start  = request.POST.get("data_start", "").strip()
        data_end    = request.POST.get("data_end", "").strip()

        # 3. Получаем IP клиента
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        client_ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")

        # 4. Объявляем переменную error заранее
        error = None

        # 5. Валидация
        if not alfa_name:
            error = "Поле Alfa Name не может быть пустым."
        elif not mother_id:
            error = "Нужно выбрать материнскую компанию."
        # сюда можно добавить проверки на price, currency и т.д.

        # 6. Если есть ошибка — возвращаем форму обратно
        if error:
            messages.error(request, error)
            return render(request, "alfa_add.html", {
                "mothers": mothers,
                "prev_alfa_name": alfa_name,
                "prev_mother_id": mother_id,
                "prev_price": price,
                "prev_currency": currency,
                "prev_fee": fee,
                "prev_data_start": data_start,
                "prev_data_end": data_end,
            })

        # 7. Вычисляем новый ID
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM descr.alfa_numbers_new;")
            new_id = cursor.fetchone()[0] + 1

        # 8. Вставляем запись
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO descr.alfa_numbers_new 
                  (id, alfa_name, id_company, price, currency, fee,
                   data_start, data_end, ips)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, [
                new_id,
                alfa_name,
                int(mother_id),
                price,
                currency,
                fee,
                data_start,
                data_end,
                client_ip,  # единственный IP
            ])

        messages.success(request, "Alfa-номер добавлен.")
        return redirect("sms_blinoff:alfa_list")

    # GET — отрисовываем пустую форму
    return render(request, "alfa_add.html", {
        "mothers": mothers,
        "prev_alfa_name": "",
        "prev_mother_id": "",
        "prev_price": "",
        "prev_currency": "",
        "prev_fee": "",
        "prev_data_start": "",
        "prev_data_end": "",
    })


def sms_services(request):
    """
    Список из descr.service_new с подцеплённым именем матери.
    """
    with connections['pgDataforSMS'].cursor() as c:
        c.execute("""
            SELECT
              N.id,
              mother_id    AS mother_id,
              M.name       AS mother_name,
              N.descr,
              N.agreement,
              N.price,
              N.currency,
              N.type,
              N.created_at,
              N.ip_address
            from descr.service_new N
left join descr.mother M on
n.mother_id = M.id
            ORDER BY N.id;
        """)
        cols = [col[0] for col in c.description]
        rows = [dict(zip(cols, row)) for row in c.fetchall()]

    return render(request, "sms_services.html", {
        "services": rows,
    })


def category3_list(request):
    """
    Показывает все строки из SMSc.Category_3.
    """
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("""
            SELECT name_3, price
            FROM "SMSc"."Category_3"
            ORDER BY name_3;
        """)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, "category3_list.html", {
        "categories": rows,
    })


def paymed_sms_list(request):
    """
    Показывает все строки из SMSc.Category_3.
    """
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("""
            SELECT
                    P.*,
                    C.name       AS company_name  -- или любые нужные вам поля из C
                    FROM payments.paymed_sms AS P
                    LEFT JOIN descr.companies   AS C
                        ON P.comp_id = C.id;
        """)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, "paymed_sms_list.html", {
        "payments": rows,
    })   


def sms_periode(request, period=None):
    # 1) Определяем даты
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    if period:
        try:
            start_str, end_str = period.split("-")
            start_date = datetime.datetime.strptime(start_str, "%Y.%m.%d").date()
            end_date   = datetime.datetime.strptime(end_str,   "%Y.%m.%d").date()
        except ValueError:
            messages.error(request, "Неправильный формат периода, ожидается YYYY.MM.DD-YYYY.MM.DD")
            return redirect("sms_blinoff:sms_periode")
    else:
        start_date = yesterday
        end_date   = today

    # 2) Выполняем запрос
    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute("""
            SELECT
              date_trunc('day', dt_hour)      AS day,
              C.name                          AS name_sq,
              H.num_cg_direction,
              H.num_cd_direction,
              V.name                          AS name_sd,
              SUM(H.count_amount)             AS total_count
            FROM sms.hourly_stats_blinoff H
            LEFT JOIN description.companies C
              ON H.num_cg_direction = C.id
            LEFT JOIN description.companies V
              ON H.num_cd_direction = V.id
            WHERE dt_hour >= %s
              AND dt_hour <  %s + INTERVAL '1 day'
            GROUP BY 1,2,3,4,5
            ORDER BY 1,2,3,4,5;
        """, [start_date, end_date])
        cols = [c[0] for c in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, "hour_sms_blinoff.html", {
        "rows": rows,
        "start": start_date,
        "end":   end_date,
    })

