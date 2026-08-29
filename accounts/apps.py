from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Importing models here ensures the @receiver decorator in
        # models.py actually runs and registers the signal, since
        # Django calls ready() once during startup
        import accounts.models
