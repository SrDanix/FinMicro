from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from . import auditoria  # noqa: F401  (conecta las señales de inicio de sesión, RF-32)
