from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Student (public) endpoints
    path('', views.chat_landing, name='landing'),
    path('student/<str:chat_id>/', views.student_chat, name='student_chat'),
    
    # Technician endpoints
    path('dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('join/<str:chat_id>/', views.join_chat, name='join_chat'),
    path('tech/<str:chat_id>/', views.technician_chat, name='technician_chat'),
    
    # API endpoints
    path('api/messages/<str:chat_id>/', views.chat_messages_api, name='messages_api'),
    path('api/download/<int:attachment_id>/', views.download_attachment, name='download_attachment'),
]
