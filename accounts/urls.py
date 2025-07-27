from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetView

urlpatterns = [
    # Login/Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset
    path('password-reset/',
        CustomPasswordResetView.as_view(),
        name='password_reset'),
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'),
    path('reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'),

    # User Management
    path('users/', views.manage_users, name='manage_users'),
    path('users/add-technician/', views.add_technician, name='add_technician'),
    path('users/add-manager/', views.add_system_manager, name='add_system_manager'),
    path('users/toggle/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # 📅 NEW SCHEDULE MANAGEMENT URLS
    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('schedule/update/<int:day_of_week>/', views.update_day_schedule, name='update_day_schedule'),
    path('schedule/overrides/', views.manage_schedule_overrides, name='manage_schedule_overrides'),
    path('schedule/overrides/delete/<int:override_id>/', views.delete_schedule_override, name='delete_schedule_override'),
    path('schedule/status/', views.schedule_status_api, name='schedule_status_api'),
]