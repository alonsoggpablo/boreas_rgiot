# boreas_bot/routers.py
# Ensures all boreas_bot models use the 'external' database

class BoreasBotRouter:
    app_label = 'boreas_bot'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'external'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'external'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label == self.app_label or
            obj2._meta.app_label == self.app_label
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == 'external'
        return None
