from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ChatSession, ChatMessage

@receiver(post_save, sender=ChatMessage)
def handle_new_message(sender, instance, created, **kwargs):
    """🌊 Handle new message events"""
    if created:
        # Could trigger real-time notifications here
        # Example: WebSocket notifications, email alerts, etc.
        pass

@receiver(post_delete, sender=ChatSession)
def cleanup_chat_files(sender, instance, **kwargs):
    """🧹 Clean up files when chat is deleted"""
    # Files are automatically deleted by Django's FileField
    # This is just for additional cleanup if needed
    pass