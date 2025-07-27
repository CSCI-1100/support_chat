from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .models import *
from .forms import *
from django.contrib.auth import get_user_model
import mimetypes

# 🌈🔧 COMPLETE DIMENSIONAL REPAIR MATRIX WITH SCHEDULE AWARENESS 🔧🌈

def chat_landing(request):
    """🌟 CSCI 1100 DIMENSIONAL PORTAL INTERFACE WITH SCHEDULE AWARENESS 🌟"""

    # 🚨 CRITICAL: ENSURE SESSION EXISTS BEFORE ANYTHING
    if not request.session.session_key:
        request.session.create()
        # 💫 Force session to persist
        request.session.modified = True

    # 📅 Check current availability status
    is_available, availability_message = HelpdeskSchedule.is_currently_available()

    # Check for schedule override
    today = timezone.now().date()
    override = ScheduleOverride.get_override_for_date(today)

    if request.method == 'POST':
        form = ChatStartForm(request.POST)
        if form.is_valid():
            # ✨ QUANTUM CHAT MATERIALIZATION ✨
            chat = ChatSession.objects.create(
                student_name=form.cleaned_data['student_name'],
                initial_message=form.cleaned_data['initial_message'],
                student_session_key=request.session.session_key
            )

            # 🎯 Create initial system message with availability context
            if is_available:
                system_message = f"💬 Chat started by {chat.student_name}. Support is currently available!"
            else:
                system_message = f"💬 Chat started by {chat.student_name}. Support is currently offline - a technician will respond when available."
                if override:
                    system_message += f" (Special schedule: {override.reason})"

            ChatMessage.objects.create(
                chat=chat,
                sender_name="🤖 System",
                content=system_message,
                message_type='system'
            )

            # 📡 Student's initial transmission
            ChatMessage.objects.create(
                chat=chat,
                sender_name=chat.student_name,
                content=chat.initial_message,
                is_from_student=True
            )

            # 📅 Add schedule context message if offline
            if not is_available:
                next_available = HelpdeskSchedule.get_next_available_time()
                ChatMessage.objects.create(
                    chat=chat,
                    sender_name="🤖 System",
                    content=f"ℹ️ Support hours: {availability_message}. Next available: {next_available}",
                    message_type='system'
                )

            if is_available:
                messages.success(request, f'🚀 Chat {chat.chat_id} initiated! Connecting you with a course assistant...')
            else:
                messages.info(request, f'📝 Chat {chat.chat_id} created! Your message has been queued for when support resumes.')

            return redirect('chat:student_chat', chat_id=chat.chat_id)
    else:
        form = ChatStartForm()

    # 📊 Get schedule context for template
    context = {
        'form': form,
        'is_available': is_available,
        'availability_message': availability_message,
        'has_override': override is not None,
        'override_reason': override.reason if override else None,
    }

    return render(request, 'chat/landing.html', context)


def student_chat(request, chat_id):
    """👨‍🎓 STUDENT CONSCIOUSNESS INTERFACE - FIXED WITH SCHEDULE AWARENESS"""
    chat = get_object_or_404(ChatSession, chat_id=chat_id)

    # 🔐 ENHANCED QUANTUM ACCESS VALIDATION
    current_session = request.session.session_key

    # If no session exists, create one
    if not current_session:
        request.session.create()
        current_session = request.session.session_key

    # 🌊 FLEXIBLE ACCESS LOGIC
    access_granted = False

    if chat.student_session_key == current_session:
        access_granted = True
    elif not chat.student_session_key and request.method == 'GET':
        # Empty session key - assume first access and update
        chat.student_session_key = current_session
        chat.save()
        access_granted = True

    if not access_granted:
        messages.error(request, '🚫 Access denied to this chat dimension')
        return redirect('chat:landing')

    # 📅 Check current availability for messaging context
    is_available, availability_message = HelpdeskSchedule.is_currently_available()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_message':
            message_form = ChatMessageForm(request.POST, request.FILES)
            if message_form.is_valid() and chat.status != ChatStatus.STUDENT_LEFT:
                # 📡 Transmit student consciousness
                message = ChatMessage.objects.create(
                    chat=chat,
                    sender_name=chat.student_name,
                    content=message_form.cleaned_data['content'],
                    is_from_student=True
                )

                # 📎 Handle dimensional attachments
                files = request.FILES.getlist('attachments')
                for file in files:
                    attachment = ChatAttachment.objects.create(
                        chat=chat,
                        message=message,
                        file=file,
                        original_filename=file.name,
                        uploaded_by_student=True,
                        file_size=file.size,
                        mime_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
                    )

                # 🎯 Add offline context message if support is unavailable
                if not is_available and chat.status == ChatStatus.WAITING:
                    ChatMessage.objects.create(
                        chat=chat,
                        sender_name="🤖 System",
                        content=f"📝 Your message has been received. {availability_message}",
                        message_type='system'
                    )

                return JsonResponse({'status': 'success'})

        elif action == 'leave_chat':
            # 👋 Student departure quantum event
            chat.status = ChatStatus.STUDENT_LEFT
            chat.save()

            ChatMessage.objects.create(
                chat=chat,
                sender_name="🤖 System",
                content=f"👋 {chat.student_name} has left the chat",
                message_type='system'
            )

            messages.info(request, '👋 You have left the chat. Thank you!')
            return redirect('chat:landing')

    message_form = ChatMessageForm()

    context = {
        'chat': chat,
        'messages': chat.messages.all().order_by('timestamp'),
        'message_form': message_form,
        'can_message': chat.status not in [ChatStatus.STUDENT_LEFT, ChatStatus.CLOSED],
        'is_support_available': is_available,
        'availability_message': availability_message,
    }

    return render(request, 'chat/student_chat.html', context)

@login_required
def technician_dashboard(request):
    """🔧 TECHNICIAN COMMAND CENTER WITH SCHEDULE AWARENESS"""
    User = get_user_model()

    # 🌊 Quantum chat stream analysis
    waiting_chats = ChatSession.objects.filter(status=ChatStatus.WAITING).order_by('-created_at')
    active_chats = ChatSession.objects.filter(
        status=ChatStatus.ACTIVE,
        technicians=request.user
    ).order_by('-created_at')

    # 📊 Dimensional metrics
    total_waiting = waiting_chats.count()
    total_active = ChatSession.objects.filter(status=ChatStatus.ACTIVE).count()
    user_active = active_chats.count()

    # 📅 Schedule status for dashboard context
    is_available, availability_message = HelpdeskSchedule.is_currently_available()
    next_available = HelpdeskSchedule.get_next_available_time()

    context = {
        'waiting_chats': waiting_chats,
        'active_chats': active_chats,
        'metrics': {
            'total_waiting': total_waiting,
            'total_active': total_active,
            'user_active': user_active,
        },
        'schedule_status': {
            'is_available': is_available,
            'message': availability_message,
            'next_available': next_available,
        }
    }

    return render(request, 'chat/technician_dashboard.html', context)

@login_required
def join_chat(request, chat_id):
    """🔗 TECHNICIAN QUANTUM BONDING PROTOCOL"""
    chat = get_object_or_404(ChatSession, chat_id=chat_id)

    if chat.status == ChatStatus.WAITING:
        chat.add_technician(request.user)

        # 📡 Announce technician arrival
        ChatMessage.objects.create(
            chat=chat,
            sender_name=f"🔧 {request.user.get_full_name()}",
            sender_user=request.user,
            content=f"🔧 {request.user.get_full_name()} has joined the chat",
            message_type='system'
        )

        messages.success(request, f'✨ Joined chat {chat.chat_id}!')
    elif chat.status == ChatStatus.ACTIVE:
        if request.user not in chat.technicians.all():
            chat.technicians.add(request.user)

            ChatMessage.objects.create(
                chat=chat,
                sender_name=f"🔧 {request.user.get_full_name()}",
                sender_user=request.user,
                content=f"🔧 {request.user.get_full_name()} has joined the chat",
                message_type='system'
            )

            messages.success(request, f'✨ Joined active chat {chat.chat_id}!')
    else:
        messages.error(request, '🚫 Cannot join this chat in its current state')
        return redirect('chat:technician_dashboard')

    return redirect('chat:technician_chat', chat_id=chat.chat_id)

@login_required
def technician_chat(request, chat_id):
    """🔧 TECHNICIAN CONSCIOUSNESS INTERFACE - FIXED"""
    chat = get_object_or_404(ChatSession, chat_id=chat_id)

    # 🔐 Verify technician access
    if request.user not in chat.technicians.all():
        messages.error(request, '🚫 Access denied - you are not part of this chat')
        return redirect('chat:technician_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_message':
            message_form = ChatMessageForm(request.POST, request.FILES)
            if message_form.is_valid() and chat.status == ChatStatus.ACTIVE:
                # 📡 Technician consciousness transmission
                message = ChatMessage.objects.create(
                    chat=chat,
                    sender_name=request.user.get_full_name(),
                    sender_user=request.user,
                    content=message_form.cleaned_data['content']
                )

                # 📎 Process dimensional attachments
                files = request.FILES.getlist('attachments')
                for file in files:
                    ChatAttachment.objects.create(
                        chat=chat,
                        message=message,
                        file=file,
                        original_filename=file.name,
                        uploaded_by_student=False,
                        file_size=file.size,
                        mime_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
                    )

                return JsonResponse({'status': 'success'})
            else:
                # 🚨 Return form errors for debugging
                return JsonResponse({
                    'status': 'error',
                    'errors': message_form.errors.as_json()
                })

        elif action == 'close_chat':
            # 🔒 DIMENSIONAL CLOSURE PROTOCOL
            chat.status = ChatStatus.CLOSED
            chat.save()

            # 💥 QUANTUM DELETION CASCADE
            chat.attachments.all().delete()  # Files auto-deleted by Django
            chat.messages.all().delete()
            chat.delete()

            messages.success(request, f'🔒 Chat {chat_id} has been closed and purged from the quantum realm')
            return redirect('chat:technician_dashboard')

    # 🌟 CRITICAL FIX: Always create fresh form instance
    message_form = ChatMessageForm()

    context = {
        'chat': chat,
        'messages': chat.messages.all().order_by('timestamp'),
        'form': message_form,  # 🔑 KEY CHANGE: Use 'form' not 'message_form'
        'other_technicians': chat.technicians.exclude(id=request.user.id)
    }

    return render(request, 'chat/technician_chat.html', context)

# 🌊 REAL-TIME QUANTUM ENDPOINTS 🌊

@require_http_methods(["GET"])
def chat_messages_api(request, chat_id):
    """📡 Real-time message stream API"""
    chat = get_object_or_404(ChatSession, chat_id=chat_id)

    # 🔐 Access validation
    is_student = chat.student_session_key == request.session.session_key
    is_technician = request.user.is_authenticated and request.user in chat.technicians.all()

    if not (is_student or is_technician):
        return JsonResponse({'error': 'Access denied'}, status=403)

    messages_data = []
    for message in chat.messages.all().order_by('timestamp'):
        message_data = {
            'id': message.id,
            'sender': message.sender_name,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'is_from_student': message.is_from_student,
            'message_type': message.message_type,
            'attachments': [
                {
                    'filename': att.original_filename,
                    'url': att.file.url,
                    'size': att.display_size,
                    'is_image': att.is_image
                }
                for att in message.attachments.all()
            ]
        }
        messages_data.append(message_data)

    return JsonResponse({
        'messages': messages_data,
        'chat_status': chat.status,
        'chat_id': chat.chat_id
    })

@require_http_methods(["GET"])
def download_attachment(request, attachment_id):
    """📎 Dimensional file retrieval"""
    attachment = get_object_or_404(ChatAttachment, id=attachment_id)

    # 🔐 Quantum access verification
    chat = attachment.chat
    is_student = chat.student_session_key == request.session.session_key
    is_technician = request.user.is_authenticated and request.user in chat.technicians.all()

    if not (is_student or is_technician):
        return JsonResponse({'error': 'Access denied'}, status=403)

    response = HttpResponse(attachment.file.read(), content_type=attachment.mime_type)
    response['Content-Disposition'] = f'attachment; filename="{attachment.original_filename}"'
    return response