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
from .decorators import group_required 
from django.views.decorators.http import require_http_methods
from datetime import datetime
from decimal import Decimal
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


def dfNumbersPrice(request):
    with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute('''
                select
                        DN.id,
                        Dn.id_comp,
                        M.name,
                        DN.price,
                        DN.valid_from,
                        DN.valid_to
                        from  descr.defnumbersprice_new DN
                        left join descr.mother M
                        on DN.id_comp = M.id
                        order by 2
                            ;
                    
        ''')
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'dfNumbersList.html', {'companies': rows})


@group_required('addMother', redirect_to='sms_blinoff:mother_list', message="У вас нет прав для добавления записи.")
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


@group_required('addMother', redirect_to='sms_blinoff:mother_list', message="У вас нет прав для добавления записи.")
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


@group_required('canDelMother', redirect_to='sms_blinoff:mother_list', message="У вас нет прав для удаления записей.")
def delete_mother(request, id):
    try:
        with connections['pgDataforSMS'].cursor() as cursor:
            # Получаем имя удаляемой записи
            cursor.execute('SELECT id, name FROM descr.mother WHERE id = %s', [id])
            row = cursor.fetchone()
            if not row:
                messages.error(request, 'Запись не найдена.')
                return redirect('sms_blinoff:mother_list')

            id = row[0]
            name = row[1]

            # Удаляем запись из agrements.reestr
            cursor.execute('DELETE FROM descr.mother WHERE id = %s', [id])

            # Логируем в descr.mother_deleted
            cursor.execute('''
                INSERT INTO descr.mother_deleted (id_del ,name, user_del)
                VALUES (%s,%s, %s)
            ''', [id,name, request.user.username])

        messages.success(request, f'Запись {name} успешно удалена.')
        return redirect('sms_blinoff:mother_list')

    except Exception as e:
        messages.error(request, f'Ошибка при удалении: {e}')
        return redirect('sms_blinoff:mother_list')
   



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

def edit_alfa(request, alfa_id):
    # Получаем текущую запись
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("""
            SELECT id, alfa_name, id_company, price, currency, fee,
                   data_start, data_end
            FROM descr.alfa_numbers_new
            WHERE id = %s;
        """, [alfa_id])
        row = cursor.fetchone()

        if not row:
            messages.error(request, "Alfa-номер не найден.")
            return redirect("sms_blinoff:alfa_list")

        current = {
            "id": row[0],
            "alfa_name": row[1],
            "id_company": row[2],
            "price": float(row[3]),
            "currency": row[4],
            "fee": float(row[5]),
            "data_start": row[6].date() if isinstance(row[6], datetime) else row[6],
            "data_end": row[7].date() if isinstance(row[7], datetime) else row[7],
        }

    # Загружаем список материнских компаний
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name FROM descr.mother ORDER BY name;")
        mothers = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    if request.method == "POST":
        # Обновлённые данные из формы
        updated = {
            "alfa_name": request.POST.get("alfa_name", "").strip(),
            "id_company": int(request.POST.get("mother_id", "").strip()),
            "price": float(request.POST.get("price", "0").strip() or 0),
            "currency": request.POST.get("currency", "").strip(),
            "fee": float(request.POST.get("fee", "0").strip() or 0),
            "data_start": request.POST.get("data_start", "").strip(),
            "data_end": request.POST.get("data_end", "").strip(),
        }

        # IP пользователя
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        client_ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")

        # Преобразуем даты
        try:
            updated["data_start"] = datetime.fromisoformat(updated["data_start"]).date()
        except ValueError:
            updated["data_start"] = current["data_start"]

        try:
            updated["data_end"] = datetime.fromisoformat(updated["data_end"]).date()
        except ValueError:
            updated["data_end"] = current["data_end"]

        # Проверка на изменения
        changed = (
            updated["alfa_name"] != current["alfa_name"] or
            updated["id_company"] != current["id_company"] or
            updated["price"] != current["price"] or
            updated["currency"] != current["currency"] or
            updated["fee"] != current["fee"] or
            updated["data_start"] != current["data_start"] or
            updated["data_end"] != current["data_end"]
        )

        if changed:
            # Обновляем запись
            with connections['pgDataforSMS'].cursor() as cursor:
                cursor.execute("""
                    UPDATE descr.alfa_numbers_new
                    SET alfa_name = %s,
                        id_company = %s,
                        price = %s,
                        currency = %s,
                        fee = %s,
                        data_start = %s,
                        data_end = %s
                    WHERE id = %s;
                """, [
                    updated["alfa_name"],
                    updated["id_company"],
                    updated["price"],
                    updated["currency"],
                    updated["fee"],
                    updated["data_start"],
                    updated["data_end"],
                    alfa_id
                ])

                # Запись в историю
                cursor.execute("""
                    INSERT INTO descr.alfa_numbers_new_history (
                        alfa_id,
                        alfa_name_old, alfa_name_new,
                        price_old, price_new,
                        currency_old, currency_new,
                        fee_old, fee_new,
                        data_start_old, data_start_new,
                        data_end_old, data_end_new,
                        changed_by_ip, changed_by_user
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, [
                    alfa_id,
                    current["alfa_name"], updated["alfa_name"],
                    current["price"], updated["price"],
                    current["currency"], updated["currency"],
                    current["fee"], updated["fee"],
                    current["data_start"], updated["data_start"],
                    current["data_end"], updated["data_end"],
                    client_ip,
                    request.user.username if request.user.is_authenticated else "anonymous"
                ])

            messages.success(request, "Изменения сохранены.")
        else:
            messages.info(request, "Изменений не обнаружено.")

        return redirect("sms_blinoff:alfa_list")

    # GET — отобразить форму
    return render(request, "alfa_edit.html", {
        "mothers": mothers,
        "alfa": current,
    })





@require_http_methods(["GET", "POST"])
def bulk_edit_alfa(request):
    # 1. Получаем список ID
    if request.method == "POST":
        id_list = [int(i) for i in request.POST.getlist("ids") if i.strip().isdigit()]
    else:  # GET
        id_list = [int(i) for i in request.GET.get("ids", "").split(",") if i.strip().isdigit()]

    if not id_list:
        messages.warning(request, "Вы не выбрали ни одной записи.")
        return redirect("sms_blinoff:alfa_list")

    # 2. Получаем список компаний
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name FROM descr.mother ORDER BY name;")
        mothers = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    # 3. Обработка изменений
    if request.method == "POST" and 'apply_changes' in request.POST:
        def parse_float(val):
            try:
                return float(val.replace(",", ".").strip())
            except:
                return None

        def parse_date(val):
            try:
                return datetime.fromisoformat(val).date()
            except:
                return None

        new_fields = {
            "price": parse_float(request.POST.get("price")),
            "currency": request.POST.get("currency", "").strip() or None,
            "fee": parse_float(request.POST.get("fee")),
            "data_start": parse_date(request.POST.get("data_start")),
            "data_end": parse_date(request.POST.get("data_end")),
            "id_company": int(request.POST.get("mother_id")) if request.POST.get("mother_id") else None,
        }

        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        client_ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")
        username = request.user.username if request.user.is_authenticated else "anonymous"

        updated_count = 0

        with connections['pgDataforSMS'].cursor() as cursor:
            for alfa_id in id_list:
                cursor.execute("SELECT * FROM descr.alfa_numbers_new WHERE id = %s;", [alfa_id])
                row = cursor.fetchone()
                if not row:
                    continue

                colnames = [desc[0] for desc in cursor.description]
                old = dict(zip(colnames, row))

                updates = {}
                for key, new_val in new_fields.items():
                    if new_val is None:
                        continue

                    old_val = old.get(key)
                    if isinstance(old_val, Decimal):
                        try:
                            old_val = float(old_val)
                        except:
                            pass
                    if isinstance(old_val, datetime):
                        old_val = old_val.date()
                    if isinstance(new_val, datetime):
                        new_val = new_val.date()

                    if new_val != old_val:
                        updates[key] = new_val

                if updates:
                    set_clause = ", ".join([f"{k} = %s" for k in updates])
                    values = list(updates.values()) + [alfa_id]
                    cursor.execute(f"""
                        UPDATE descr.alfa_numbers_new
                        SET {set_clause}
                        WHERE id = %s;
                    """, values)

                    cursor.execute("""
                        INSERT INTO descr.alfa_numbers_new_history (
                            alfa_id,
                            alfa_name_old, alfa_name_new,
                            price_old, price_new,
                            currency_old, currency_new,
                            fee_old, fee_new,
                            data_start_old, data_start_new,
                            data_end_old, data_end_new,
                            changed_at, changed_by_ip, changed_by_user
                        ) VALUES (
                            %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            NOW(), %s, %s
                        );
                    """, [
                        old["id"],
                        old["alfa_name"], old["alfa_name"],
                        old["price"], updates.get("price", old["price"]),
                        old["currency"], updates.get("currency", old["currency"]),
                        old["fee"], updates.get("fee", old["fee"]),
                        old["data_start"], updates.get("data_start", old["data_start"]),
                        old["data_end"], updates.get("data_end", old["data_end"]),
                        client_ip,
                        username
                    ])
                    updated_count += 1

        messages.success(request, f"Обновлено {updated_count} записей.")
        return redirect("sms_blinoff:alfa_list")

    return render(request, "alfa_bulk_edit.html", {
        "ids": id_list,
        "mothers": mothers
    })



def copy_alfa(request, alfa_id):
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("""
            SELECT id, alfa_name, id_company, price, currency, fee,
                   data_start, data_end
            FROM descr.alfa_numbers_new
            WHERE id = %s;
        """, [alfa_id])
        row = cursor.fetchone()

        if not row:
            messages.error(request, "Исходный Alfa-номер не найден.")
            return redirect("sms_blinoff:alfa_list")

        original = dict(zip(
            ["id", "alfa_name", "id_company", "price", "currency", "fee", "data_start", "data_end"],
            row
        ))

    # Загружаем список компаний
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name FROM descr.mother ORDER BY name;")
        mothers = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    if request.method == "POST":
        # Чтение формы
        new_data = {
            "alfa_name": request.POST.get("alfa_name", "").strip(),
            "id_company": int(request.POST.get("mother_id", "").strip()),
            "price": float(request.POST.get("price", 0)),
            "currency": request.POST.get("currency", "").strip(),
            "fee": float(request.POST.get("fee", 0)),
            "data_start": request.POST.get("data_start", "").strip(),
            "data_end": request.POST.get("data_end", "").strip(),
        }

        # IP
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        client_ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")

        with connections['pgDataforSMS'].cursor() as cursor:
            # Новый ID
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM descr.alfa_numbers_new;")
            new_id = cursor.fetchone()[0] + 1

            cursor.execute("""
                INSERT INTO descr.alfa_numbers_new (
                    id, alfa_name, id_company, price, currency, fee,
                    data_start, data_end, ips
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, [
                new_id,
                new_data["alfa_name"],
                new_data["id_company"],
                new_data["price"],
                new_data["currency"],
                new_data["fee"],
                new_data["data_start"],
                new_data["data_end"],
                client_ip
            ])

        messages.success(request, "Новая копия успешно создана.")
        return redirect("sms_blinoff:alfa_list")

    # GET — показать форму
    return render(request, "alfa_copy.html", {
        "alfa": original,
        "mothers": mothers
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



def showIDReestrandMother(request):
    """
    Показывает все строки из SMSc.Category_3.
    """
    with connections['pg_consolidation'].cursor() as cursor:
        cursor.execute("""
            select I.*, R.contractor, M.name from agrements.ids I
            left join agrements.reestr R  on
            i.id_agr= R.id
            left join  description.mother M  on
            i.mother_id = M.id
            order by 2
        """)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, "idsList.html", {
        "ids": rows,
    })   


def add_defNumbers(request):
    # 1. Подгружаем только те компании, у которых ЕЩЁ НЕТ DN-номеров
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("""
            SELECT M.id, M.name
            FROM descr.mother M
            WHERE NOT EXISTS (
                SELECT 1 FROM descr.defnumbersprice_new DN
                WHERE DN.id_comp = M.id
            )
            ORDER BY M.name;
        """)
        mothers = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    if request.method == "POST":
        # 2. Читаем форму
        mother_id   = request.POST.get("mother_id", "").strip()
        price       = request.POST.get("price", "").strip()
        valid_from  = request.POST.get("valid_from", "").strip()
        valid_to    = request.POST.get("valid_to", "").strip()

        # 3. Валидация
        error = None
        if not mother_id:
            error = "Не выбрана компания."
        elif not price:
            error = "Не указана цена."

        if error:
            messages.error(request, error)
            return render(request, "defnumbers_add.html", {
                "mothers": mothers,
                "prev_mother_id": mother_id,
                "prev_price": price,
                "prev_valid_from": valid_from,
                "prev_valid_to": valid_to,
            })

        # 4. Вычисляем новый ID
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM descr.defnumbersprice_new;")
            new_id = cursor.fetchone()[0] + 1

        # 5. Вставляем запись
        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO descr.defnumbersprice_new
                  (id, id_comp, price, valid_from, valid_to)
                VALUES (%s, %s, %s, %s, %s);
            """, [
                new_id,
                int(mother_id),
                price,
                valid_from if valid_from else None,
                valid_to if valid_to else None,
            ])

        messages.success(request, "DN-номер успешно добавлен.")
        return redirect("sms_blinoff:dfNumbersPrice")

    # GET — отрисовываем форму
    return render(request, "defnumbers_add.html", {
        "mothers": mothers,
        "prev_mother_id": "",
        "prev_price": "",
        "prev_valid_from": "",
        "prev_valid_to": "",
    })

 
#@group_required('addAlfa', redirect_to='sms_blinoff:alfa_list', message="У вас нет прав для добавления записей.")
def bulk_add_alfa(request):
    # 1. Загружаем список материнских компаний
    with connections['pgDataforSMS'].cursor() as cursor:
        cursor.execute("SELECT id, name FROM descr.mother ORDER BY name;")
        mothers = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

    if request.method == "POST":
        alfa_names = request.POST.getlist("alfa_names[]")
        mother_id = request.POST.get("mother_id", "").strip()
        price = request.POST.get("price", "").strip()
        currency = request.POST.get("currency", "").strip()
        fee = request.POST.get("fee", "").strip()
        data_start = request.POST.get("data_start", "").strip()
        data_end = request.POST.get("data_end", "").strip()

        # Получаем IP
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        client_ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")

        # Проверка на пустые поля
        if not alfa_names or not any(name.strip() for name in alfa_names):
            messages.error(request, "Введите хотя бы один Alfa-номер.")
            return render(request, "alfa_bulk_add.html", {
                "mothers": mothers,
                "prev_alfa_names": alfa_names,
                "prev_mother_id": mother_id,
                "prev_price": price,
                "prev_currency": currency,
                "prev_fee": fee,
                "prev_data_start": data_start,
                "prev_data_end": data_end,
            })

        if not mother_id:
            messages.error(request, "Выберите материнскую компанию.")
            return render(request, "alfa_bulk_add.html", {
                "mothers": mothers,
                "prev_alfa_names": alfa_names,
                "prev_mother_id": mother_id,
                "prev_price": price,
                "prev_currency": currency,
                "prev_fee": fee,
                "prev_data_start": data_start,
                "prev_data_end": data_end,
            })

        with connections['pgDataforSMS'].cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM descr.alfa_numbers_new;")
            last_id = cursor.fetchone()[0]

            count = 0
            for name in alfa_names:
                name = name.strip()
                if not name:
                    continue

                last_id += 1
                cursor.execute("""
                    INSERT INTO descr.alfa_numbers_new
                        (id, alfa_name, id_company, price, currency, fee,
                         data_start, data_end, ips)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, [
                    last_id,
                    name,
                    int(mother_id),
                    price or None,
                    currency or None,
                    fee or None,
                    data_start or None,
                    data_end or None,
                    client_ip,
                ])
                count += 1

        messages.success(request, f"Добавлено {count} Alfa-номеров.")
        return redirect("sms_blinoff:alfa_list")

    # GET-запрос — рендерим пустую форму
    return render(request, "alfa_bulk_add.html", {
        "mothers": mothers,
        "prev_alfa_names": [""],
        "prev_mother_id": "",
        "prev_price": "",
        "prev_currency": "",
        "prev_fee": "",
        "prev_data_start": "",
        "prev_data_end": "",
    })
