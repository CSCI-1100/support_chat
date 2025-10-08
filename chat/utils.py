import mimetypes
import os
from django.core.files.storage import default_storage
from django.conf import settings

def get_file_icon(filename):
    """Get appropriate icon for file type"""
    mime_type, _ = mimetypes.guess_type(filename)
    
    if not mime_type:
        return 'bi-file-earmark'
    
    icon_map = {
        'image/': 'bi-image',
        'video/': 'bi-camera-video',
        'audio/': 'bi-music-note',
        'application/pdf': 'bi-file-earmark-pdf',
        'application/msword': 'bi-file-earmark-word',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'bi-file-earmark-word',
        'application/vnd.ms-excel': 'bi-file-earmark-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'bi-file-earmark-excel',
        'application/zip': 'bi-file-earmark-zip',
        'text/': 'bi-file-earmark-text',
    }
    
    for mime_prefix, icon in icon_map.items():
        if mime_type.startswith(mime_prefix) or mime_type == mime_prefix.rstrip('/'):
            return icon
    
    return 'bi-file-earmark'

def cleanup_orphaned_files():
    """
    Clean up orphaned attachment files"""
    # Implementation for cleaning up files that are no longer referenced
    # This would be called by a periodic task
    pass

def validate_chat_access(request, chat):
    """Validate user access to chat"""
    # For students: check session key
    if not request.user.is_authenticated:
        return chat.student_session_key == request.session.session_key
    
    # For technicians: check if they're part of the chat
    return request.user in chat.technicians.all()

class ChatPermissions:
    """Chat permission checker"""
    
    @staticmethod
    def can_join_chat(user, chat):
        """Check if technician can join a chat"""
        return (
            user.is_authenticated and 
            hasattr(user, 'user_type') and 
            user.user_type in ['TCH', 'MGR']
        )
    
    @staticmethod
    def can_close_chat(user, chat):
        """Check if user can close a chat"""
        return (
            user.is_authenticated and 
            user in chat.technicians.all()
        )
    
    @staticmethod
    def can_send_message(user, chat, is_student=False):
        """Check if user can send messages"""
        if is_student:
            return chat.status == chat.ChatStatus.ACTIVE
        
        return (
            user.is_authenticated and 
            user in chat.technicians.all() and
            chat.status == chat.ChatStatus.ACTIVE
        )
