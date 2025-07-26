from django import forms
from django.contrib.auth.forms import UserCreationForm
from custom_validators.validators import *
from django.core.exceptions import ValidationError
from .models import User, SystemManager
from django.contrib.auth.forms import AuthenticationForm
from django.utils.html import mark_safe

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
