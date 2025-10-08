from django.db import models
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
import os
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatStatus(models.TextChoices):
    WAITING = 'WAIT', '⏳ Waiting for Technician'
    ACTIVE = 'ACTV', '💬 Active Chat'
    STUDENT_LEFT = 'LEFT', '👋 Student Left'
    CLOSED = 'CLSD', '🔒 Closed'

def generate_chat_id():
    """Generate unique chat identifier"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    return f"CHAT-{timestamp}-{random_suffix}"

class ChatSession(models.Model):
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
        # Validate user exists in database before attempting foreign key relationship
        if not u or not u.pk:
            raise ValueError("🚫 Cannot add unsaved or None user to chat session")

        self.technicians.add(u)
        if self.status == ChatStatus.WAITING:
            self.status = ChatStatus.ACTIVE
            self.save()

    def cleanup_files(self):
        """Clean up all files associated with this chat"""
        try:
            # Get all attachments for this chat
            attachments = self.attachments.all()
            deleted_count = 0

            for attachment in attachments:
                try:
                    # Delete the actual file from disk
                    if attachment.file and os.path.isfile(attachment.file.path):
                        os.remove(attachment.file.path)
                        deleted_count += 1
                        logger.info(f"Deleted file: {attachment.file.path}")

                    # Delete the attachment record
                    attachment.delete()

                except Exception as e:
                    logger.error(f"Error deleting file {attachment.original_filename}: {str(e)}")
                    # Continue with other files even if one fails
                    continue

            # Try to clean up empty directories
            self._cleanup_empty_directories()

            logger.info(f"Chat {self.chat_id}: Cleaned up {deleted_count} files")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during file cleanup for chat {self.chat_id}: {str(e)}")
            return 0

    def _cleanup_empty_directories(self):
        """Remove empty directories in the chat attachments path"""
        try:
            from django.conf import settings

            # Get the media root and chat attachments path
            media_root = settings.MEDIA_ROOT
            chat_path = os.path.join(media_root, 'chat_attachments')

            # Walk through directories and remove empty ones
            for root, dirs, files in os.walk(chat_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # Only remove if directory is empty
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            logger.debug(f"Removed empty directory: {dir_path}")
                    except OSError:
                        # Directory not empty or other error, skip
                        pass

        except Exception as e:
            logger.debug(f"Error cleaning up directories: {str(e)}")

    def delete(self, *args, **kwargs):
        """Override delete to clean up files first"""
        self.cleanup_files()
        super().delete(*args, **kwargs)

class ChatMessage(models.Model):
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

    # Message enhancement fields
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
    """Dimensional file entities"""
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
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def is_image(self):
        """Check if file is an image"""
        return self.mime_type.startswith('image/') if self.mime_type else False

    def delete(self, *args, **kwargs):
        """Override delete to clean up file"""
        try:
            if self.file and os.path.isfile(self.file.path):
                os.remove(self.file.path)
                logger.info(f"Deleted attachment file: {self.file.path}")
        except Exception as e:
            logger.error(f"Error deleting attachment file: {str(e)}")

        super().delete(*args, **kwargs)

class HelpdeskSchedule(models.Model):
    """Weekly schedule for helpdesk availability"""

    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, unique=True)
    is_active = models.BooleanField(default=False, help_text="Is support available on this day?")
    start_time = models.TimeField(null=True, blank=True, help_text="When support starts (24-hour format)")
    end_time = models.TimeField(null=True, blank=True, help_text="When support ends (24-hour format)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_updates'
    )

    class Meta:
        ordering = ['day_of_week']
        verbose_name = "Helpdesk Schedule"
        verbose_name_plural = "Helpdesk Schedules"

    def __str__(self):
        day_name = self.get_day_of_week_display()
        if self.is_active and self.start_time and self.end_time:
            return f"{day_name}: {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
        elif self.is_active:
            return f"{day_name}: Active (no time restrictions)"
        else:
            return f"{day_name}: Closed"

    def clean(self):
        """Validate that if active, start/end times are provided and logical"""
        if self.is_active:
            if not self.start_time or not self.end_time:
                raise ValidationError("Active days must have both start and end times specified.")

            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def is_currently_available(cls):
        """Check if support is currently available based on schedule"""
        now = timezone.localtime()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()

        try:
            day_schedule = cls.objects.get(day_of_week=current_day)

            if not day_schedule.is_active:
                return False, f"Support is closed on {day_schedule.get_day_of_week_display()}s"

            if not day_schedule.start_time or not day_schedule.end_time:
                return True, "Support is available"

            if day_schedule.start_time <= current_time <= day_schedule.end_time:
                return True, "Support is currently available"
            else:
                return False, f"Support hours: {day_schedule.start_time.strftime('%I:%M %p')} - {day_schedule.end_time.strftime('%I:%M %p')}"

        except cls.DoesNotExist:
            # No schedule configured for this day - default to closed
            return False, "Schedule not configured for this day"

    @classmethod
    def get_next_available_time(cls):
        """Get the next time support will be available"""
        now = timezone.localtime()
        current_day = now.weekday()
        current_time = now.time()

        # Check remaining time today
        try:
            today_schedule = cls.objects.get(day_of_week=current_day, is_active=True)
            if (today_schedule.start_time and today_schedule.end_time and
                current_time < today_schedule.start_time):
                return f"Today at {today_schedule.start_time.strftime('%I:%M %p')}"
        except cls.DoesNotExist:
            pass

        # Check next 7 days
        for i in range(1, 8):
            check_day = (current_day + i) % 7
            try:
                schedule = cls.objects.get(day_of_week=check_day, is_active=True)
                if schedule.start_time:
                    day_name = dict(cls.DAYS_OF_WEEK)[check_day]
                    if i == 1:
                        return f"Tomorrow ({day_name}) at {schedule.start_time.strftime('%I:%M %p')}"
                    else:
                        return f"{day_name} at {schedule.start_time.strftime('%I:%M %p')}"
            except cls.DoesNotExist:
                continue

        return "Schedule not available"

    @classmethod
    def initialize_default_schedule(cls):
        """Create default schedule (Monday-Friday 9AM-5PM)"""
        default_schedules = [
            # Monday-Friday: 9 AM - 5 PM
            (0, True, datetime.time(9, 0), datetime.time(17, 0)),   # Monday
            (1, True, datetime.time(9, 0), datetime.time(17, 0)),   # Tuesday
            (2, True, datetime.time(9, 0), datetime.time(17, 0)),   # Wednesday
            (3, True, datetime.time(9, 0), datetime.time(17, 0)),   # Thursday
            (4, True, datetime.time(9, 0), datetime.time(17, 0)),   # Friday
            # Weekend: Closed
            (5, False, None, None),  # Saturday
            (6, False, None, None),  # Sunday
        ]

        for day, active, start, end in default_schedules:
            cls.objects.get_or_create(
                day_of_week=day,
                defaults={
                    'is_active': active,
                    'start_time': start,
                    'end_time': end
                }
            )


class ScheduleOverride(models.Model):
    """Special schedule overrides for holidays, events, etc."""

    date = models.DateField(unique=True)
    is_active = models.BooleanField(default=False, help_text="Is support available on this specific date?")
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, help_text="Why this override exists (e.g., 'Holiday', 'Extended hours for finals')")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_overrides'
    )

    class Meta:
        ordering = ['date']
        verbose_name = "Schedule Override"
        verbose_name_plural = "Schedule Overrides"

    def __str__(self):
        if self.is_active and self.start_time and self.end_time:
            return f"{self.date}: {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')} ({self.reason})"
        elif self.is_active:
            return f"{self.date}: Open ({self.reason})"
        else:
            return f"{self.date}: Closed ({self.reason})"

    def clean(self):
        if self.is_active and (not self.start_time or not self.end_time):
            raise ValidationError("Active override days must have both start and end times.")

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    @classmethod
    def get_override_for_date(cls, date):
        """Get schedule override for a specific date"""
        try:
            return cls.objects.get(date=date)
        except cls.DoesNotExist:
            return None