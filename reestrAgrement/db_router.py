class ReestrRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'reestr':
            return 'pg_consolidation'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'reestr':
            return 'pg_consolidation'
        return None

class DefaultOnlyRouter:
    """
    Позволяет выполнять миграции и операции только на БД 'default'.
    Для всех прочих баз — запрет.
    """
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # «default» — это ваша sqlite; для неё всё по-прежнему можно мигрировать
        if db == 'default':
            return True
        # для любой другой БД (postgres) — миграции запрещены
        return False

    # (Опционально: если у вас есть чтение/запись, можно ещё явно маршрутизировать запросы)
    def db_for_read(self, model, **hints):
        return 'default'
    def db_for_write(self, model, **hints):
        return 'default'