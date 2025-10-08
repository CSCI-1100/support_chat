# chat/management/commands/init_schedule.py

from django.core.management.base import BaseCommand
from chat.models import HelpdeskSchedule
import datetime

class Command(BaseCommand):
    help = 'Initialize default helpdesk schedule (Mon-Fri 9AM-5PM)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force initialization even if schedules already exist',
        )
        parser.add_argument(
            '--business-hours',
            action='store_true',
            help='Set up standard business hours (9 AM - 5 PM, Mon-Fri)',
        )
        parser.add_argument(
            '--extended-hours',
            action='store_true', 
            help='Set up extended hours (8 AM - 8 PM, Mon-Fri)',
        )
        parser.add_argument(
            '--finals-week',
            action='store_true',
            help='Set up finals week hours (8 AM - 10 PM, Mon-Sun)',
        )

    def handle(self, *args, **options):
        # Check if schedules already exist
        existing_count = HelpdeskSchedule.objects.count()
        
        if existing_count > 0 and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'📅 Schedule already exists ({existing_count} days configured). '
                    'Use --force to reinitialize.'
                )
            )
            return

        # Determine which schedule to create
        if options['extended_hours']:
            schedule_type = 'extended'
            start_time = datetime.time(9, 0)
            end_time = datetime.time(18, 0)
            active_days = [0, 1, 2, 3, 4]  # Mon-Fri
            self.stdout.write('🕐 Creating extended hours schedule...')
            
        elif options['finals_week']:
            schedule_type = 'finals'
            start_time = datetime.time(9, 0)
            end_time = datetime.time(19, 0)
            active_days = [0, 1, 2, 3, 4]  # Mon-Fri
            self.stdout.write('📚 Creating finals week schedule...')
            
        else:  # Default to business hours
            schedule_type = 'business'
            start_time = datetime.time(9, 0)
            end_time = datetime.time(16, 30)
            active_days = [0, 1, 2, 3, 4]  # Mon-Fri
            self.stdout.write('🏢 Creating business hours schedule...')

        # Create/update schedule for all days
        created_count = 0
        updated_count = 0
        
        for day in range(7):  # 0=Monday, 6=Sunday
            is_active = day in active_days
            
            schedule, created = HelpdeskSchedule.objects.get_or_create(
                day_of_week=day,
                defaults={
                    'is_active': is_active,
                    'start_time': start_time if is_active else None,
                    'end_time': end_time if is_active else None,
                }
            )
            
            if created:
                created_count += 1
                day_name = dict(HelpdeskSchedule.DAYS_OF_WEEK)[day]
                if is_active:
                    self.stdout.write(f'  ✅ {day_name}: {start_time.strftime("%I:%M %p")} - {end_time.strftime("%I:%M %p")}')
                else:
                    self.stdout.write(f'  ❌ {day_name}: Closed')
            else:
                # Update existing if force flag is set
                if options['force']:
                    schedule.is_active = is_active
                    schedule.start_time = start_time if is_active else None
                    schedule.end_time = end_time if is_active else None
                    schedule.save()
                    updated_count += 1
                    day_name = dict(HelpdeskSchedule.DAYS_OF_WEEK)[day]
                    if is_active:
                        self.stdout.write(f'  🔄 {day_name}: {start_time.strftime("%I:%M %p")} - {end_time.strftime("%I:%M %p")} (updated)')
                    else:
                        self.stdout.write(f'  🔄 {day_name}: Closed (updated)')

        # Summary
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created schedule for {created_count} day(s)')
            )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'🔄 Updated schedule for {updated_count} day(s)')
            )
        
        if created_count == 0 and updated_count == 0:
            self.stdout.write(
                self.style.WARNING('⚠️ No changes made. Use --force to overwrite existing schedule.')
            )
        
        # Show current status
        self.stdout.write('\n📊 Current Schedule Status:')
        is_available, message = HelpdeskSchedule.is_currently_available()
        if is_available:
            self.stdout.write(self.style.SUCCESS(f'🟢 {message}'))
        else:
            self.stdout.write(self.style.WARNING(f'🔴 {message}'))
            next_available = HelpdeskSchedule.get_next_available_time()
            self.stdout.write(f'   Next available: {next_available}')

# Example usage:
# python manage.py init_schedule                    # Business hours (default: 9 AM - 4:30 PM)
# python manage.py init_schedule --extended-hours   # 9 AM - 6 PM, Mon-Fri
# python manage.py init_schedule --finals-week      # 9 AM - 7 PM, Mon-Fri
# python manage.py init_schedule --force            # Overwrite existing