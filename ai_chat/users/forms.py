# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

class CustomUserChangeForm(UserChangeForm):
    """Form for editing user profile"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture', 
                 'bio', 'location', 'website']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class UserPreferencesForm(forms.Form):
    """Form for editing user preferences"""
    AI_MODEL_CHOICES = [
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('gpt-4', 'GPT-4'),
        ('claude-3-opus', 'Claude 3 Opus'),
        ('claude-3-sonnet', 'Claude 3 Sonnet'),
        ('local-llama', 'Local LLaMA (Requires Setup)'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default'),
    ]
    
    # App appearance
    theme = forms.ChoiceField(choices=THEME_CHOICES, initial='system')
    enable_animations = forms.BooleanField(required=False, initial=True)
    compact_view = forms.BooleanField(required=False, initial=False)
    
    # AI settings
    default_ai_model = forms.ChoiceField(choices=AI_MODEL_CHOICES, initial='gpt-3.5-turbo')
    default_temperature = forms.FloatField(
        initial=0.7,
        min_value=0.1,
        max_value=1.0,
        widget=forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'max': '1.0'})
    )
    default_max_tokens = forms.IntegerField(
        initial=800,
        min_value=100,
        max_value=4000,
        widget=forms.NumberInput(attrs={'step': '50', 'min': '100', 'max': '4000'})
    )
    
    # Interface preferences
    auto_save_conversations = forms.BooleanField(required=False, initial=True)
    enable_markdown = forms.BooleanField(required=False, initial=True)
    enable_code_highlighting = forms.BooleanField(required=False, initial=True)
    enable_message_timestamps = forms.BooleanField(required=False, initial=True)
    
    # Notification preferences
    email_notifications = forms.BooleanField(required=False, initial=False)
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Initialize from user preferences if they exist
        if user.preferences:
            for key, value in user.preferences.items():
                if key in self.fields:
                    self.fields[key].initial = value
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def save(self):
        """Save preferences to user's preferences JSON field"""
        preferences = {}
        for field_name, field in self.fields.items():
            preferences[field_name] = self.cleaned_data.get(field_name)
        
        self.user.preferences = preferences
        self.user.save(update_fields=['preferences'])
        return self.user