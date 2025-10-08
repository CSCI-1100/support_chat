from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class UserType(models.TextChoices):
        SYSTEM_MANAGER = 'MGR', 'System Manager'
        TECHNICIAN = 'TCH', 'Technician'

    user_type = models.CharField(
        max_length=3,
        choices=UserType.choices,
        default=UserType.TECHNICIAN
    )
    department = models.CharField(max_length=100)

    # Override groups and user_permissions with custom related_names
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class SystemManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=100)
    departments = models.CharField(max_length=200)  # Comma-separated departments
    technicians = models.ManyToManyField(User, related_name='managed_by')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.job_title}"

    def get_departments_list(self):
        return self.departments.split(',')

    def get_departments_str(self):
        departments = self.departments.split(',')
        return ", ".join(departments)