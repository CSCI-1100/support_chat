from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    verbose_name = '💬 Chat Support System'

    def ready(self):
        """🌟 Initialize chat system consciousness"""
        pass
        # Import signals if needed
        # import chat.signals
