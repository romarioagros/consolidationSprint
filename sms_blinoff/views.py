from django.shortcuts import render
from django.contrib import messages

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
