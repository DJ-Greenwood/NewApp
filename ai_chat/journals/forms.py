from django import forms
from .models import Journal, JournalEntry, JournalTemplate, JournalPrompt

class JournalForm(forms.ModelForm):
    """Form for creating and editing journals"""
    
    class Meta:
        model = Journal
        fields = ['title', 'description', 'journal_type', 'character']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter journal title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Provide a brief description of your journal',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'journal_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'character': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class JournalEntryForm(forms.ModelForm):
    """Form for creating and editing journal entries"""
    
    # Tags field for handling the JSON field
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter tags separated by commas',
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        }),
        help_text="Optional: Add tags separated by commas (e.g., 'reflection, goals, ideas')"
    )
    
    class Meta:
        model = JournalEntry
        fields = ['title', 'entry_date', 'mood', 'location', 'content', 'characters']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter entry title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'mood': forms.TextInput(attrs={
                'placeholder': 'How are you feeling?',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Where are you?',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your journal entry here...',
                'rows': 15,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'characters': forms.SelectMultiple(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have an instance with tags, initialize the tags_input field
        if self.instance and self.instance.pk and self.instance.tags:
            self.fields['tags_input'].initial = ', '.join(self.instance.tags)
    
    def clean_tags_input(self):
        """Process the tags input into a list for the JSON field"""
        tags_text = self.cleaned_data.get('tags_input', '')
        
        if not tags_text:
            return []
        
        # Split by commas and strip whitespace
        tags = [tag.strip() for tag in tags_text.split(',')]
        
        # Remove empty tags
        tags = [tag for tag in tags if tag]
        
        return tags
    
    def save(self, commit=True):
        """Override save to handle the tags field"""
        instance = super().save(commit=False)
        
        # Set tags from the processed tags_input
        instance.tags = self.cleaned_data.get('tags_input', [])
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class JournalTemplateForm(forms.ModelForm):
    """Form for creating and editing journal templates"""
    
    class Meta:
        model = JournalTemplate
        fields = ['title', 'template_type', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter template title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'template_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Enter template content. Use {{placeholders}} for dynamic content.',
                'rows': 10,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class JournalPromptForm(forms.ModelForm):
    """Form for creating custom journal prompts"""
    
    class Meta:
        model = JournalPrompt
        fields = ['text', 'category']
        widgets = {
            'text': forms.Textarea(attrs={
                'placeholder': 'Enter your prompt question or idea',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }