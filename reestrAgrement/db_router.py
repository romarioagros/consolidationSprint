class ReestrRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'reestr':
            return 'pg_consolidation'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'reestr':
            return 'pg_consolidation'
        return None
