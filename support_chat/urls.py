from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from chat import views

handler404 = 'chat.views.handle_404'

def smart_root_redirect(request):
    """🧠 Intelligent routing based on user type"""
    if request.user.is_authenticated:
        # Authenticated users go to technician dashboard
        return redirect('chat:technician_dashboard')
    else:
        # Anonymous users go to student chat landing
        return redirect('chat:landing')

urlpatterns = [
    # 🔧 Admin interface
    path('admin/', admin.site.urls),

    # 💬 Main chat system
    path('', smart_root_redirect, name='root'),
    path('chat/', include('chat.urls')),

    # 🔐 Keep accounts for technician login
    path('accounts/', include('accounts.urls')),
]

# 📁 Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)