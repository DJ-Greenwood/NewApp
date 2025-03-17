from django import forms
from .models import Story, Chapter, StoryNote

class StoryForm(forms.ModelForm):
    """Form for creating and editing stories"""
    
    class Meta:
        model = Story
        fields = ['title', 'description', 'genre', 'characters', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter story title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Provide a brief description of your story',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'genre': forms.TextInput(attrs={
                'placeholder': 'E.g., Fantasy, Sci-Fi, Mystery',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'characters': forms.SelectMultiple(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber focus:ring-amber'
            }),
        }
        help_texts = {
            'is_public': 'Make this story visible to other users (coming soon)'
        }


class ChapterForm(forms.ModelForm):
    """Form for creating and editing chapters"""
    
    class Meta:
        model = Chapter
        fields = ['title', 'content', 'characters']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter chapter title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your chapter content here',
                'rows': 15,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'characters': forms.SelectMultiple(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class StoryNoteForm(forms.ModelForm):
    """Form for creating and editing story notes"""
    
    class Meta:
        model = StoryNote
        fields = ['title', 'content', 'note_type', 'character']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter note title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your note content here',
                'rows': 8,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'note_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'character': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }