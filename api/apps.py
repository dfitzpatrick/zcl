from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        super(ApiConfig, self).ready()
        import api.signals # Load signals
