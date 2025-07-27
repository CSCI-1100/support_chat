from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, SystemManager
from django.contrib.auth.forms import AuthenticationForm
from django.utils.html import mark_safe
from chat.models import HelpdeskSchedule, ScheduleOverride
import datetime

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control shadow-none',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control shadow-none',
            'placeholder': 'Password'
        })

class TechnicianCreationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control shadow-none'})
    )
    class Meta:
        model = User
        # Remove if username/password is not needed for tech
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'department')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
            'department': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@etsu.edu'):
            raise ValidationError('Please use an ETSU email address.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.UserType.TECHNICIAN
        if commit:
            user.save()
        return user

class SystemManagerCreationForm(UserCreationForm):
    departments = forms.CharField(
        max_length=200,
        help_text='Comma-separated list of departments',
        widget=forms.TextInput(attrs={'class': 'form-control shadow-none'})
    )
    job_title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control shadow-none'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control shadow-none'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control shadow-none'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@etsu.edu'):
            raise ValidationError('Please use an ETSU email address.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.UserType.SYSTEM_MANAGER
        if commit:
            user.save()
            SystemManager.objects.create(
                user=user,
                job_title=self.cleaned_data['job_title'],
                departments=self.cleaned_data['departments']
            )
        return user

class HelpdeskScheduleForm(forms.ModelForm):
    """📅 Form for configuring weekly helpdesk schedule"""

    class Meta:
        model = HelpdeskSchedule
        fields = ['day_of_week', 'is_active', 'start_time', 'end_time']
        widgets = {
            'day_of_week': forms.HiddenInput(),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input day-active-checkbox',
                'data-day': '',  # Will be set in view
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control time-input',
                'type': 'time',
                'step': '900',  # 15-minute intervals
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control time-input',
                'type': 'time',
                'step': '900',  # 15-minute intervals
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial checkbox state and data attribute
        if self.instance and hasattr(self.instance, 'day_of_week'):
            self.fields['is_active'].widget.attrs['data-day'] = self.instance.day_of_week

        # Make time fields conditional on is_active
        if not self.instance.is_active:
            self.fields['start_time'].required = False
            self.fields['end_time'].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if is_active:
            if not start_time:
                raise ValidationError({'start_time': 'Start time is required when day is active.'})
            if not end_time:
                raise ValidationError({'end_time': 'End time is required when day is active.'})

            if start_time and end_time and start_time >= end_time:
                raise ValidationError({'end_time': 'End time must be after start time.'})

        return cleaned_data


class BulkScheduleForm(forms.Form):
    """📅 Form for setting schedule for multiple days at once"""

    PRESET_SCHEDULES = [
        ('', '-- Select a preset --'),
        ('business_hours', 'Business Hours (9 AM - 4:30 PM, Mon-Fri)'),
        ('extended_hours', 'Extended Hours (9 AM - 6 PM, Mon-Fri)'),
        ('weekend_support', 'Weekend Support (10 AM - 3 PM, Sat-Sun)'),
        ('finals_week', 'Finals Week (9 AM - 7 PM, Mon-Fri)'),
        ('all_closed', 'All Days Closed'),
    ]

    preset = forms.ChoiceField(
        choices=PRESET_SCHEDULES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'preset-selector'
        }),
        help_text="Quick presets to apply to selected days"
    )

    apply_to_days = forms.MultipleChoiceField(
        choices=HelpdeskSchedule.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Select which days to apply the preset to"
    )

    def apply_preset(self, user=None):
        """Apply the selected preset to the selected days"""
        preset = self.cleaned_data.get('preset')
        days = self.cleaned_data.get('apply_to_days', [])

        if not preset or not days:
            return 0

        preset_configs = {
            'business_hours': {'is_active': True, 'start_time': datetime.time(9, 0), 'end_time': datetime.time(16, 30)},
            'extended_hours': {'is_active': True, 'start_time': datetime.time(9, 0), 'end_time': datetime.time(18, 0)},
            'weekend_support': {'is_active': True, 'start_time': datetime.time(10, 0), 'end_time': datetime.time(15, 0)},
            'finals_week': {'is_active': True, 'start_time': datetime.time(9, 0), 'end_time': datetime.time(19, 0)},
            'all_closed': {'is_active': False, 'start_time': None, 'end_time': None},
        }

        config = preset_configs.get(preset, {})
        updated_count = 0

        for day_num_str in days:
            day_num = int(day_num_str)
            schedule, created = HelpdeskSchedule.objects.get_or_create(
                day_of_week=day_num,
                defaults=config
            )

            if not created:
                # Update existing schedule
                for field, value in config.items():
                    setattr(schedule, field, value)
                if user:
                    schedule.updated_by = user
                schedule.save()

            updated_count += 1

        return updated_count


class ScheduleOverrideForm(forms.ModelForm):
    """📅 Form for creating schedule overrides for specific dates"""

    class Meta:
        model = ScheduleOverride
        fields = ['date', 'is_active', 'start_time', 'end_time', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': datetime.date.today().isoformat(),  # Can't create overrides for past dates
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'override-active'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'step': '900',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'step': '900',
            }),
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., "Holiday", "Extended hours for finals", "Staff training day"',
                'maxlength': 200
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].required = True

        # Make time fields conditional
        if self.instance and not self.instance.is_active:
            self.fields['start_time'].required = False
            self.fields['end_time'].required = False

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < datetime.date.today():
            raise ValidationError("Cannot create overrides for past dates.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if is_active:
            if not start_time:
                raise ValidationError({'start_time': 'Start time is required when override is active.'})
            if not end_time:
                raise ValidationError({'end_time': 'End time is required when override is active.'})

            if start_time and end_time and start_time >= end_time:
                raise ValidationError({'end_time': 'End time must be after start time.'})

        return cleaned_data