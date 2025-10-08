from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import ChatSession, ChatMessage, ChatAttachment
import os
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ChatMessage)
def handle_new_message(sender, instance, created, **kwargs):
    """Handle new message events"""
    if created:
        # Could trigger real-time notifications here
        # Example: WebSocket notifications, email alerts, etc.
        logger.info(f"New message in chat {instance.chat.chat_id} from {instance.sender_name}")

@receiver(pre_delete, sender=ChatSession)
def cleanup_chat_files_before_delete(sender, instance, **kwargs):
    """Clean up files before chat session is deleted"""
    try:
        # Clean up all files associated with this chat
        deleted_count = instance.cleanup_files()
        logger.info(f"Chat {instance.chat_id} cleanup: {deleted_count} files removed before deletion")
    except Exception as e:
        logger.error(f"Error cleaning up files for chat {instance.chat_id}: {str(e)}")

@receiver(post_delete, sender=ChatSession)
def handle_chat_deletion(sender, instance, **kwargs):
    """Handle post-deletion cleanup for chat sessions"""
    logger.info(f"Chat session {instance.chat_id} has been permanently deleted")

@receiver(pre_delete, sender=ChatAttachment)
def cleanup_attachment_file(sender, instance, **kwargs):
    """Clean up individual attachment files when attachment is deleted"""
    try:
        if instance.file and os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
            logger.info(f"Deleted attachment file: {instance.file.path}")
    except Exception as e:
        logger.error(f"Error deleting attachment file {instance.original_filename}: {str(e)}")

@receiver(post_delete, sender=ChatAttachment)
def handle_attachment_deletion(sender, instance, **kwargs):
    """Handle post-deletion cleanup for attachments"""
    logger.debug(f"Attachment {instance.original_filename} deleted from chat {instance.chat.chat_id}")

# Batch cleanup utilities for maintenance
def cleanup_orphaned_files():
    """Clean up orphaned files that have no database record"""
    from django.conf import settings
    import glob

    try:
        # Get all file paths from database
        db_files = set()
        for attachment in ChatAttachment.objects.all():
            if attachment.file:
                db_files.add(attachment.file.path)

        # Get all files in chat_attachments directory
        media_root = settings.MEDIA_ROOT
        chat_files_pattern = os.path.join(media_root, 'chat_attachments', '**', '*')
        disk_files = glob.glob(chat_files_pattern, recursive=True)

        # Remove files that exist on disk but not in database
        orphaned_count = 0
        for file_path in disk_files:
            if os.path.isfile(file_path) and file_path not in db_files:
                try:
                    os.remove(file_path)
                    orphaned_count += 1
                    logger.info(f"Removed orphaned file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing orphaned file {file_path}: {str(e)}")

        logger.info(f"Cleanup completed: {orphaned_count} orphaned files removed")
        return orphaned_count

    except Exception as e:
        logger.error(f"Error during orphaned file cleanup: {str(e)}")
        return 0

def cleanup_old_chat_files(days_old=7):
    """Clean up files from chats older than specified days"""
    from django.utils import timezone
    from datetime import timedelta

    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)

        # Find old closed chats
        old_chats = ChatSession.objects.filter(
            status=ChatSession.ChatStatus.CLOSED,
            created_at__lt=cutoff_date
        )

        total_cleaned = 0
        for chat in old_chats:
            cleaned_count = chat.cleanup_files()
            total_cleaned += cleaned_count
            # Delete the chat session itself
            chat.delete()

        logger.info(f"Cleaned up {total_cleaned} files from {old_chats.count()} old chats")
        return total_cleaned

    except Exception as e:
        logger.error(f"Error during old chat cleanup: {str(e)}")
        return 0
