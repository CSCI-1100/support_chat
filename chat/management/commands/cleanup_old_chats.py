from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatSession

class Command(BaseCommand):
    help = '🧹 Clean up old closed chat sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete closed chats older than this many days (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find old closed chats
        old_chats = ChatSession.objects.filter(
            status=ChatSession.ChatStatus.CLOSED,
            created_at__lt=cutoff_date
        )
        
        count = old_chats.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'🔍 DRY RUN: Would delete {count} closed chats older than {days} days'
                )
            )
            for chat in old_chats[:10]:  # Show first 10
                self.stdout.write(f'  - {chat.chat_id} ({chat.student_name}) - {chat.created_at}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            old_chats.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Successfully deleted {count} old closed chats'
                )
            )
