from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from accounts.models import SystemManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a new system manager account'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the system manager')
        parser.add_argument('email', type=str, help='Email address (must be @etsu.edu)')
        parser.add_argument('password', type=str, help='Password for the account')
        parser.add_argument('first_name', type=str, help='First name')
        parser.add_argument('last_name', type=str, help='Last name')
        parser.add_argument('job_title', type=str, help='Job title')
        parser.add_argument('departments', type=str, help='Comma-separated list of departments')

        # Optional arguments
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if a system manager already exists',
        )

    def handle(self, *args, **options):
        # Check if system manager already exists
        if SystemManager.objects.exists() and not options['force']:
            raise CommandError(
                'A system manager already exists. Use --force to create anyway.'
            )

        # Validate email
        try:
            validate_email(options['email'])
            if not options['email'].endswith('@etsu.edu'):
                raise CommandError('Email must be an @etsu.edu address')
        except ValidationError:
            raise CommandError('Invalid email address')

        try:
            # Create user
            user = User.objects.create_user(
                username=options['username'],
                email=options['email'],
                password=options['password'],
                first_name=options['first_name'],
                last_name=options['last_name'],
                user_type=User.UserType.SYSTEM_MANAGER
            )

            # Create system manager profile
            SystemManager.objects.create(
                user=user,
                job_title=options['job_title'],
                departments=options['departments']
            )

            self.stdout.write(self.style.SUCCESS(
                f'Successfully created system manager "{options["username"]}"'
            ))
            self.stdout.write(
                'You can now log in to the admin interface with these credentials.'
            )

        except Exception as e:
            # Clean up if something goes wrong
            if 'user' in locals():
                user.delete()
            raise CommandError(f'Failed to create system manager: {str(e)}')

# Example usage:
# python manage.py create_system_manager username email@etsu.edu password "First" "Last" "Systems Manager" "Computing,Digital Media"