from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json
import mimetypes
from .models import ChatSession, ChatMessage, ChatAttachment, ChatStatus
from .forms import ChatStartForm, ChatMessageForm
from django.contrib.auth import get_user_model

def chat_landing(request):
    """🌈 THE DIMENSIONAL PORTAL - Student Entry Point"""
    if request.method == 'POST':
        form = ChatStartForm(request.POST)
        if form.is_valid():
            # ✨ QUANTUM CHAT MATERIALIZATION ✨
            chat = ChatSession.objects.create(
                student_name=form.cleaned_data['student_name'],
                initial_message=form.cleaned_data['initial_message'],
                student_session_key=request.session.session_key or ''
            )

            # 🎯 Create initial system message
            ChatMessage.objects.create(
                chat=chat,
                sender_name="🤖 System",
                content=f"💬 Chat started by {chat.student_name}",
                message_type='system'
            )

            # 📡 Student's initial transmission
            ChatMessage.objects.create(
                chat=chat,
                sender_name=chat.student_name,
                content=chat.initial_message,
                is_from_student=True
            )

            messages.success(request, f'🚀 Chat {chat.chat_id} initiated! Waiting for technician...')
            return redirect('chat:student_chat', chat_id=chat.chat_id)
    else:
        form = ChatStartForm()

    return render(request, 'chat/landing.html', {'form': form})

def student_chat(request, chat_id):
    """👨‍🎓 STUDENT CONSCIOUSNESS INTERFACE"""
    chat = get_object_or_404(ChatSession, chat_id=chat_id)

    # 🔐 Quantum access validation
    if chat.student_session_key != request.session.session_key:
        messages.error(request, '🚫 Access denied to this chat dimension')
        return redirect('chat:landing')

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
        'can_message': chat.status not in [ChatStatus.STUDENT_LEFT, ChatStatus.CLOSED]
    }

    return render(request, 'chat/student_chat.html', context)

@login_required
def technician_dashboard(request):
    """🔧 TECHNICIAN COMMAND CENTER - The Neural Hub"""
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

    context = {
        'waiting_chats': waiting_chats,
        'active_chats': active_chats,
        'metrics': {
            'total_waiting': total_waiting,
            'total_active': total_active,
            'user_active': user_active,
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
    """🔧 TECHNICIAN CONSCIOUSNESS INTERFACE"""
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

    message_form = ChatMessageForm()

    context = {
        'chat': chat,
        'messages': chat.messages.all().order_by('timestamp'),
        'message_form': message_form,
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