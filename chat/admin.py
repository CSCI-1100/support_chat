from django.contrib import admin
from .models import ChatSession, ChatMessage, ChatAttachment

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['chat_id', 'student_name', 'status', 'created_at', 'technician_count']
    list_filter = ['status', 'created_at']
    search_fields = ['chat_id', 'student_name', 'initial_message']
    readonly_fields = ['chat_id', 'created_at', 'student_session_key']
    filter_horizontal = ['technicians']

    def technician_count(self, obj):
        return obj.technicians.count()
    technician_count.short_description = '🔧 Technicians'

    fieldsets = (
        ('💬 Chat Information', {
            'fields': ('chat_id', 'student_name', 'status', 'created_at')
        }),
        ('📝 Content', {
            'fields': ('initial_message',)
        }),
        ('👥 Participants', {
            'fields': ('technicians', 'student_session_key')
        }),
    )

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'sender_name', 'message_type', 'timestamp', 'is_from_student']
    list_filter = ['message_type', 'is_from_student', 'timestamp']
    search_fields = ['content', 'sender_name', 'chat__chat_id']
    readonly_fields = ['timestamp']

    fieldsets = (
        ('📡 Message Info', {
            'fields': ('chat', 'sender_name', 'sender_user', 'message_type', 'is_from_student', 'timestamp')
        }),
        ('💬 Content', {
            'fields': ('content',)
        }),
    )

@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'chat', 'file_size_display', 'uploaded_at', 'uploaded_by_student']
    list_filter = ['uploaded_by_student', 'uploaded_at', 'mime_type']
    search_fields = ['original_filename', 'chat__chat_id']
    readonly_fields = ['uploaded_at', 'file_size', 'mime_type']

    def file_size_display(self, obj):
        return obj.display_size
    file_size_display.short_description = '📊 Size'
