from django.contrib import admin
from .models import ChatSession, ChatMessage, ChatAttachment, HelpdeskSchedule, ScheduleOverride

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

@admin.register(HelpdeskSchedule)
class HelpdeskScheduleAdmin(admin.ModelAdmin):
    list_display = ['get_day_name', 'is_active', 'start_time', 'end_time', 'updated_at', 'updated_by']
    list_filter = ['is_active', 'updated_at']
    ordering = ['day_of_week']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('📅 Schedule Configuration', {
            'fields': ('day_of_week', 'is_active', 'start_time', 'end_time')
        }),
        ('📊 Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()
    get_day_name.short_description = 'Day'
    get_day_name.admin_order_field = 'day_of_week'

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ScheduleOverride)
class ScheduleOverrideAdmin(admin.ModelAdmin):
    list_display = ['date', 'reason', 'is_active', 'start_time', 'end_time', 'created_by']
    list_filter = ['is_active', 'date', 'created_at']
    search_fields = ['reason', 'date']
    ordering = ['-date']
    readonly_fields = ['created_at']

    fieldsets = (
        ('📅 Override Details', {
            'fields': ('date', 'reason', 'is_active')
        }),
        ('⏰ Time Configuration', {
            'fields': ('start_time', 'end_time'),
            'description': 'Only required if override is active'
        }),
        ('📊 Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show future overrides first, then recent past ones
        return qs.extra(
            select={'is_future': "date >= CURRENT_DATE"},
            order_by=['-is_future', '-date']
        )
