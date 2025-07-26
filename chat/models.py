from django.db import models
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
import datetime
import os

User = get_user_model()

class ChatStatus(models.TextChoices):
    WAITING = 'WAIT', '⏳ Waiting for Technician'
    ACTIVE = 'ACTV', '💬 Active Chat'
    STUDENT_LEFT = 'LEFT', '👋 Student Left'
    CLOSED = 'CLSD', '🔒 Closed'

def generate_chat_id():
    """🎲 Generate quantum chat identifier"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    return f"CHAT-{timestamp}-{random_suffix}"

class ChatSession(models.Model):
    """🌟 The Dimensional Chat Entity 🌟"""
    chat_id = models.CharField(max_length=30, unique=True, default=generate_chat_id)
    student_name = models.CharField(max_length=100)
    initial_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=4,
        choices=ChatStatus.choices,
        default=ChatStatus.WAITING
    )

    # Multi-technician support 🤖✨
    technicians = models.ManyToManyField(
        'accounts.User',
        related_name='active_chats',
        blank=True
    )

    # For student reconnection without accounts
    student_session_key = models.CharField(max_length=40, blank=True)

    class Meta:
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    def __str__(self):
        return f"💬 {self.chat_id} - {self.student_name}"

    @property
    def is_active(self):
        return self.status == ChatStatus.ACTIVE

    @property
    def needs_technician(self):
        return self.status == ChatStatus.WAITING

    def add_technician(self, user):
        u = User.objects.get(pk=user.pk)
        """🔗 Quantum technician bonding"""
        # 🛡️ Validate user exists in database before attempting foreign key relationship
        if not u or not u.pk:
            raise ValueError("🚫 Cannot add unsaved or None user to chat session")

        self.technicians.add(u)
        if self.status == ChatStatus.WAITING:
            self.status = ChatStatus.ACTIVE
            self.save()

class ChatMessage(models.Model):
    """📡 Consciousness transmission entity"""
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender_name = models.CharField(max_length=100)  # Student name or technician name
    sender_user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sent_chat_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_from_student = models.BooleanField(default=False)

    # 🎭 Message enhancement fields
    message_type = models.CharField(
        max_length=10,
        choices=[
            ('text', '💬 Text'),
            ('emoji', '😊 Emoji'),
            ('system', '🤖 System'),
        ],
        default='text'
    )

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        sender = "👨‍🎓 Student" if self.is_from_student else "🔧 Tech"
        return f"{sender}: {self.content[:50]}..."

class ChatAttachment(models.Model):
    """📎 Dimensional file entities"""
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='attachments')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by_student = models.BooleanField(default=False)

    # File metadata for enhanced UX ✨
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"📎 {self.original_filename} - {self.chat.chat_id}"

    @property
    def display_size(self):
        """🔢 Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def is_image(self):
        """🖼️ Check if file is an image"""
        return self.mime_type.startswith('image/') if self.mime_type else False