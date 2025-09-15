from django.http import HttpResponse
from django.db import connections
from django.shortcuts import render
import os, math, requests
from django.conf import settings

def index(request):
    return HttpResponse("bitrix24 index OK")


API_BASE = getattr(settings, "BITRIX_WEBHOOK_BASE", "").rstrip("/")
SESSION = requests.Session()
SESSION.verify = False  # если самоподписанный SSL, как у тебя
requests.packages.urllib3.disable_warnings()  # подавим warning


def _bx_batch(cmd_map: dict, halt: int = 0):
    """
    cmd_map: {'c1': 'user.current', 'c2': 'disk.file.getExternalLink?id=123', ...}
    Возвращает (result_dict, error_dict)
    """
    payload = {'halt': halt}
    # ВАЖНО: плоские ключи 'cmd[<name>]' !
    for k, v in cmd_map.items():
        payload[f'cmd[{k}]'] = v

    r = SESSION.post(f"{API_BASE}/batch.json", data=payload, timeout=30)
    r.raise_for_status()
    j = r.json().get('result', {})
    return j.get('result') or {}, j.get('result_error') or {}




def _bitrix_external_links(object_ids):
    """
    На вход: список object_id (из bitrix_disk_index.object_id).
    На выход: {object_id: external_link or None}
    """
    links = {}
    ids = [int(x) for x in set(object_ids) if x]

    CHUNK = 50
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i+CHUNK]

        # 1) Пробуем как OBJECT
        cmd = {f'o{oid}': f'disk.object.getExternalLink?id={oid}' for oid in chunk}
        ok, err = _bx_batch(cmd)
        for k, v in ok.items():
            links[int(k[1:])] = v  # 'o2442' -> 2442

        retry = [oid for oid in chunk if oid not in links]

        # 2) Пробуем сразу как FILE (на случай, если object_id == file_id)
        if retry:
            cmd2 = {f'f{oid}': f'disk.file.getExternalLink?id={oid}' for oid in retry}
            ok2, err2 = _bx_batch(cmd2)
            for k, v in ok2.items():
                links[int(k[1:])] = v
            retry = [oid for oid in retry if oid not in links]

        # 3) Узнаём реальный FILE_ID через disk.object.get, затем ещё раз file.getExternalLink
        if retry:
            cmd3 = {f'g{oid}': f'disk.object.get?id={oid}' for oid in retry}
            ok3, err3 = _bx_batch(cmd3)

            file_map = {}
            for k, obj in ok3.items():
                oid = int(k[1:])
                if not isinstance(obj, dict):
                    continue
                # встречается FILE_ID или REAL_OBJECT_ID (у версий/симлинков)
                file_id = obj.get('FILE_ID') or obj.get('REAL_OBJECT_ID') or obj.get('ID')
                try:
                    file_map[oid] = int(file_id)
                except Exception:
                    pass

            if file_map:
                cmd4 = {f'h{oid}': f'disk.file.getExternalLink?id={fid}' for oid, fid in file_map.items()}
                ok4, err4 = _bx_batch(cmd4)
                for k, v in ok4.items():
                    links[int(k[1:])] = v

            # тем, у кого так и не вышло — None
            for oid in retry:
                links.setdefault(oid, None)

    return links






def files_list(request):
    """
    Выдаёт страницу со всеми записями из descr.alfa_numbers_new,
    присоединяя имя матери из descr.mother.
    """
    with connections['pg_consolidation'].cursor() as c:
        c.execute("""
           SELECT 
            d.object_id as id ,
            name,
            path,
            --create_time,
            to_char( (replace(create_time,'T',' ')::timestamptz AT TIME ZONE 'Europe/Moscow')
          , 'DD.MM.YYYY HH24:MI:SS') as create_time,
            to_char( (replace(update_time,'T',' ')::timestamptz AT TIME ZONE 'Europe/Moscow')
          , 'DD.MM.YYYY HH24:MI:SS') as  update_time,

         extract(epoch from d.create_time::timestamptz) AS create_ts,
         extract(epoch from d.update_time::timestamptz) AS update_ts,


            U.data->>'LAST_NAME' as created,
            U1.data->>'LAST_NAME' as updated
            FROM bitrix24.bitrix_disk_index D
            left join bitrix24.users U
            on D.created_by::text = U.data->>'ID'
            left join bitrix24.users U1
            on D.updated_by::text = U1.data->>'ID'
            where object_type = 'file'
           order by D.update_time::timestamptz desc
        """)
        cols = [col[0] for col in c.description]
        rows = [dict(zip(cols, row)) for row in c.fetchall()]
        ids = [r['id'] for r in rows if r.get('id')]
        
        links_map = _bitrix_external_links(ids)
        

        # добавляем в каждую строку
        for r in rows:
            fid = r.get('id')
            r['download_link'] = links_map.get(fid) 



    return render(request, "file_list.html", {
        "files": rows,
    })    

def user_list(request):
    """
    Выдаёт страницу со всеми записями из descr.alfa_numbers_new,
    присоединяя имя матери из descr.mother.
    """
    with connections['pg_consolidation'].cursor() as c:
        c.execute("""
           select
                data->>'ID' as id ,
                data->>'NAME' as name ,
                data->>'SECOND_NAME' as second_name ,
                data->>'LAST_NAME' as last_name ,
                data->>'EMAIL' as email ,
                data->>'WORK_PHONE' as work_phone ,
                
                 COALESCE(to_char(NULLIF(data->>'PERSONAL_BIRTHDAY','')::date, 'DD.MM.YYYY'), '')  as p_b,
                data->>'WORK_DEPARTMENT' as work_department ,
                data->>'WORK_POSITION' as work_position 
                from bitrix24.users
        """)
        cols = [col[0] for col in c.description]
        rows = [dict(zip(cols, row)) for row in c.fetchall()]
      
        



    return render(request, "users_list.html", {
        "files": rows,
    })   

 