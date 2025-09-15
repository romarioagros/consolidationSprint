from django.apps import AppConfig

class Bitgrix24Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bitrix24'   # ← строго совпадает с именем папки
    label = 'bitrix24'  # (опц.) уникальная метка