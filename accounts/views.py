from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomLoginForm, TechnicianCreationForm, SystemManagerCreationForm
from django.contrib.auth.views import PasswordResetView
from django.utils import timezone
from .models import User
from chat.models import HelpdeskSchedule, ScheduleOverride
from .forms import HelpdeskScheduleForm, BulkScheduleForm, ScheduleOverrideForm
import datetime

def is_system_manager(user):
    return user.is_authenticated and user.user_type == User.UserType.SYSTEM_MANAGER

class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_message = "We've emailed you instructions for setting your password."

    def form_valid(self, form):
        """Ensure only ETSU email addresses can request password resets"""
        email = form.cleaned_data['email']
        if not email.endswith('@etsu.edu'):
            form.add_error('email', 'Password reset is only available for ETSU email addresses.')
            return self.form_invalid(form)
        return super().form_valid(form)

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('chat:technician_dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Get the next page from the URL or default to dashboard
            next_page = request.GET.get('next', 'chat:technician_dashboard')
            return redirect(next_page)
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

def is_system_manager(user):
    """Check if user is a system manager"""
    return user.is_authenticated and user.user_type == User.UserType.SYSTEM_MANAGER

# User Management Views (these should already exist in your views.py)
@login_required
@user_passes_test(is_system_manager)
def manage_users(request):
    """View for managing users (system managers only)"""
    technicians = User.objects.filter(user_type=User.UserType.TECHNICIAN)
    system_managers = User.objects.filter(user_type=User.UserType.SYSTEM_MANAGER)

    context = {
        'technicians': technicians,
        'system_managers': system_managers,
    }
    return render(request, 'accounts/manage_users.html', context)

@login_required
@user_passes_test(is_system_manager)
def add_technician(request):
    """Add new technician (system managers only)"""
    if request.method == 'POST':
        form = TechnicianCreationForm(request.POST)
        if form.is_valid():
            technician = form.save()
            messages.success(request, f'Technician {technician.get_full_name()} created successfully.')
            return redirect('manage_users')
    else:
        form = TechnicianCreationForm()

    return render(request, 'accounts/add_technician.html', {'form': form})

@login_required
@user_passes_test(is_system_manager)
def add_system_manager(request):
    """Add new system manager (system managers only)"""
    if request.method == 'POST':
        form = SystemManagerCreationForm(request.POST)
        if form.is_valid():
            manager = form.save()
            messages.success(request, f'System Manager {manager.get_full_name()} created successfully.')
            return redirect('manage_users')
    else:
        form = SystemManagerCreationForm()

    return render(request, 'accounts/add_system_manager.html', {'form': form})

@login_required
@user_passes_test(is_system_manager)
def toggle_user_active(request, user_id):
    """Toggle user active status (system managers only)"""
    user = get_object_or_404(User, id=user_id)
    if user != request.user:  # Prevent self-deactivation
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.get_full_name()} {status} successfully.')
    else:
        messages.error(request, 'You cannot deactivate your own account.')
    return redirect('manage_users')

@login_required
@user_passes_test(is_system_manager)
def delete_user(request, user_id):
    """Delete a user (technician or system manager)"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('manage_users')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm_delete':
            # Now delete the user
            username = user.username
            user.delete()
            messages.success(request, f"User '{username}' has been permanently deleted.")
            return redirect('manage_users')
    
    # For GET request or if POST didn't process
    # Get other technicians for reassignment options
    other_technicians = User.objects.filter(user_type='TCH').exclude(id=user_id)
    
    context = {
        'user_to_delete': user,
        'other_technicians': other_technicians,
    }
    return render(request, 'accounts/delete_user.html', context)

@login_required
@user_passes_test(is_system_manager)
def manage_schedule(request):
    """📅 Main schedule management interface"""

    # Ensure all days have schedule entries
    HelpdeskSchedule.initialize_default_schedule()

    # Get all schedules ordered by day
    schedules = HelpdeskSchedule.objects.all().order_by('day_of_week')

    # Handle bulk schedule form
    bulk_form = BulkScheduleForm()
    if request.method == 'POST' and 'bulk_action' in request.POST:
        bulk_form = BulkScheduleForm(request.POST)
        if bulk_form.is_valid():
            updated_count = bulk_form.apply_preset(user=request.user)
            if updated_count > 0:
                messages.success(request, f'✅ Updated schedule for {updated_count} day(s)')
            else:
                messages.warning(request, '⚠️ No days were updated. Please select a preset and days to apply it to.')
            return redirect('manage_schedule')

    # Get recent overrides
    upcoming_overrides = ScheduleOverride.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')[:5]

    # Current availability status
    is_available, availability_message = HelpdeskSchedule.is_currently_available()
    next_available = HelpdeskSchedule.get_next_available_time()

    context = {
        'schedules': schedules,
        'bulk_form': bulk_form,
        'upcoming_overrides': upcoming_overrides,
        'is_currently_available': is_available,
        'availability_message': availability_message,
        'next_available': next_available,
        'days_of_week': dict(HelpdeskSchedule.DAYS_OF_WEEK),
    }

    return render(request, 'accounts/manage_schedule.html', context)

@login_required
@user_passes_test(is_system_manager)
def update_day_schedule(request, day_of_week):
    """📅 Update schedule for a specific day via AJAX"""

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        schedule = HelpdeskSchedule.objects.get(day_of_week=day_of_week)
    except HelpdeskSchedule.DoesNotExist:
        schedule = HelpdeskSchedule(day_of_week=day_of_week)

    form = HelpdeskScheduleForm(request.POST, instance=schedule)

    if form.is_valid():
        schedule = form.save(commit=False)
        schedule.updated_by = request.user
        schedule.save()

        return JsonResponse({
            'success': True,
            'message': f'Updated {schedule.get_day_of_week_display()} schedule',
            'schedule': {
                'day': schedule.get_day_of_week_display(),
                'is_active': schedule.is_active,
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else None,
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else None,
                'display': str(schedule)
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors,
            'message': 'Please correct the errors and try again'
        }, status=400)


@login_required
@user_passes_test(is_system_manager)
def manage_schedule_overrides(request):
    """📅 Manage schedule overrides for holidays/special events"""

    if request.method == 'POST':
        form = ScheduleOverrideForm(request.POST)
        if form.is_valid():
            override = form.save(commit=False)
            override.created_by = request.user
            override.save()

            messages.success(request, f'✅ Created schedule override for {override.date}')
            return redirect('manage_schedule_overrides')
    else:
        form = ScheduleOverrideForm()

    # Get all overrides, separated by upcoming and past
    today = timezone.now().date()
    upcoming_overrides = ScheduleOverride.objects.filter(date__gte=today).order_by('date')
    past_overrides = ScheduleOverride.objects.filter(date__lt=today).order_by('-date')[:10]

    context = {
        'form': form,
        'upcoming_overrides': upcoming_overrides,
        'past_overrides': past_overrides,
    }

    return render(request, 'accounts/manage_schedule_overrides.html', context)

@login_required
@user_passes_test(is_system_manager)
def delete_schedule_override(request, override_id):
    """📅 Delete a schedule override"""

    if request.method != 'POST':
        messages.error(request, '❌ Invalid request method')
        return redirect('manage_schedule_overrides')

    override = get_object_or_404(ScheduleOverride, id=override_id)
    date = override.date
    override.delete()

    messages.success(request, f'🗑️ Deleted schedule override for {date}')
    return redirect('manage_schedule_overrides')

def schedule_status_api(request):
    """📅 API endpoint for checking current schedule status"""

    # Check for date override first
    today = timezone.now().date()
    override = ScheduleOverride.get_override_for_date(today)

    if override:
        if override.is_active and override.start_time and override.end_time:
            current_time = timezone.localtime().time()
            is_available = override.start_time <= current_time <= override.end_time
            message = f"Special hours today: {override.start_time.strftime('%I:%M %p')} - {override.end_time.strftime('%I:%M %p')} ({override.reason})"
        else:
            is_available = override.is_active
            message = f"Special schedule today: {override.reason}"
    else:
        # Use regular schedule
        is_available, message = HelpdeskSchedule.is_currently_available()

    next_available = HelpdeskSchedule.get_next_available_time()

    # Get today's schedule for display
    today_schedule = None
    if not override:
        try:
            today_schedule = HelpdeskSchedule.objects.get(day_of_week=timezone.now().weekday())
        except HelpdeskSchedule.DoesNotExist:
            pass

    return JsonResponse({
        'is_available': is_available,
        'message': message,
        'next_available': next_available,
        'has_override': override is not None,
        'override_reason': override.reason if override else None,
        'current_time': timezone.localtime().strftime('%I:%M %p'),
        'today_schedule': {
            'is_active': today_schedule.is_active if today_schedule else False,
            'start_time': today_schedule.start_time.strftime('%I:%M %p') if today_schedule and today_schedule.start_time else None,
            'end_time': today_schedule.end_time.strftime('%I:%M %p') if today_schedule and today_schedule.end_time else None,
        } if today_schedule else None
    })
