from django.apps import AppConfig

class ASMappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ASMapp'
    verbose_name = 'Attack Surface Management'

    def ready(self):
        """Import signals when the app is ready"""
        import ASMapp.signals