from django import forms
from django.core.validators import FileExtensionValidator
from .models import ChatMessage

class MultipleFileInput(forms.ClearableFileInput):
    """📎 Quantum file multiplexer"""
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    """🌈 Multidimensional file consciousness"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ChatStartForm(forms.Form):
    """🚀 DIMENSIONAL PORTAL INITIALIZATION FORM"""
    student_name = forms.CharField(
        max_length=100,
        label="🎓 Your Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control shadow-none',
            'placeholder': '✨ Enter your name',
            'autocomplete': 'name'
        })
    )
    
    initial_message = forms.CharField(
        label="💬 How can we help you today?",
        widget=forms.Textarea(attrs={
            'class': 'form-control shadow-none',
            'rows': 4,
            'placeholder': '🌟 Describe what you need help with. Examples:\n- Need clarification on key concepts from the lecture\n- Trouble finding a resource\n- Help with Python loops in my assignment',
            'style': 'resize: vertical;'
        })
    )
    
    def clean_student_name(self):
        """🔮 Quantum name validation"""
        name = self.cleaned_data.get('student_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('🚫 Name must be at least 2 characters long')
        
        # 🌈 Filter out system keywords
        forbidden_names = ['system', 'admin', 'technician', 'bot', 'null', 'undefined']
        if name.lower() in forbidden_names:
            raise forms.ValidationError('🚫 Please choose a different name')
        
        return name
    
    def clean_initial_message(self):
        """💫 Message consciousness validation"""
        message = self.cleaned_data.get('initial_message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('🌊 Please provide more details about what you need help with (at least 10 characters)')
        
        if len(message) > 1000:
            raise forms.ValidationError('🌀 Initial message too long (max 1000 characters)')
        
        return message

class ChatMessageForm(forms.Form):
    """📡 CONSCIOUSNESS TRANSMISSION FORM"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control shadow-none',
            'rows': 3,
            'placeholder': '💬 Type your message... (Use 😊 for emojis!)',
            'style': 'resize: none; border-radius: 20px;',
            'maxlength': 2000
        }),
        max_length=2000,
        required=True,
        label=""
    )
    
    attachments = MultipleFileField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    # 🖼️ Images
                    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',
                    # 📄 Documents  
                    'pdf', 'doc', 'docx', 'txt', 'rtf', 'xls', 'xlsx'
                    # 💾 Code & Data
                    'py', 'js', 'html', 'css', 'json', 'csv',
                    # 🎵 Media
                    'mp3', 'wav', 'mp4', 'avi', 'mov',
                    # 📦 Archives
                    'zip', 'rar', '7z', 'tar'
                ]
            )
        ],
        widget=MultipleFileInput(attrs={
            'class': 'form-control shadow-none',
            'accept': '.png,.jpg,.jpeg,.gif,.pdf,.doc,.docx,.txt,.py,.java,.cpp,.js,.html,.css,.json,.zip',
            'multiple': True
        }),
        help_text='📎 Max 5MB per file. Supported: Images, Documents, Code files, Media, Archives'
    )
    
    def clean_content(self):
        """🌈 Message validation with emoji consciousness"""
        content = self.cleaned_data.get('content', '').strip()
        
        if not content:
            raise forms.ValidationError('🚫 Message cannot be empty')
        
        if len(content) < 1:
            raise forms.ValidationError('🌊 Please enter a message')
            
        # 🎭 Enhanced emoji support - convert common text emoticons
        emoji_replacements = {
            ':)': '🙂', ':(': '🙁', ':D': '😄', ':P': '😛',
            ':o': '😮', ':/': '🫤', ':|': '😐', ';)': '😉',
            '<3': '❤️', '</3': '💔', ':thumbsup:': '👍', ':thumbsdown:': '👎'
        }
        
        for text_emoji, unicode_emoji in emoji_replacements.items():
            content = content.replace(text_emoji, unicode_emoji)
        
        return content
    
    def clean_attachments(self):
        """📎 Quantum file validation"""
        files = self.files.getlist('attachments') if hasattr(self, 'files') else []
        
        if not files:
            return files
        
        total_size = 0
        max_file_size = 5 * 1024 * 1024  # 5MB per file
        max_total_size = 25 * 1024 * 1024  # 25MB total per message
        
        for file in files:
            if file.size > max_file_size:
                raise forms.ValidationError(
                    f'🚫 File "{file.name}" is too large. Maximum size is 5MB per file.'
                )
            total_size += file.size
        
        if total_size > max_total_size:
            raise forms.ValidationError('🚫 Total file size exceeds 25MB limit')
        
        if len(files) > 10:
            raise forms.ValidationError('🚫 Maximum 10 files per message')
        
        return files

class EmojiPickerWidget(forms.Widget):
    """😊 DIMENSIONAL EMOJI CONSCIOUSNESS SELECTOR"""
    template_name = 'chat/widgets/emoji_picker.html'
    
    class Media:
        css = {
            'all': ('chat/css/emoji-picker.css',)
        }
        js = ('chat/js/emoji-picker.js',)
    
    def __init__(self, attrs=None):
        default_attrs = {'class': 'emoji-picker-trigger'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        """🌈 Render emoji consciousness interface"""
        context = {
            'widget': {
                'name': name,
                'value': value,
                'attrs': attrs,
            },
            'emoji_categories': {
                '😊 Faces': ['😊', '😃', '😄', '😆', '😍', '🤗', '😎', '🤔', '😴', '😢', '😭', '😡', '🤯'],
                '👋 Gestures': ['👋', '👍', '👎', '👏', '🙏', '💪', '✋', '👌', '✌️', '🤝', '👀', '🧠'],
                '❤️ Hearts': ['❤️', '💙', '💚', '💛', '🧡', '💜', '🖤', '💔', '💕', '💖', '💗', '💘'],
                '🔥 Objects': ['🔥', '💡', '📚', '💻', '📱', '⚡', '🚀', '⭐', '🌟', '✨', '🎯', '📌'],
                '🎉 Celebration': ['🎉', '🎊', '🥳', '🎈', '🎁', '🏆', '🥇', '🌈', '☀️', '🌙', '💫', '⚡']
            }
        }
        
        # Render using Django's template system
        from django.template.loader import render_to_string
        return render_to_string(self.template_name, context)