from django import forms
from .models import Character

class CharacterForm(forms.ModelForm):
    """Form for creating and editing characters"""
    
    # Additional fields that aren't directly on the model
    traits_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter character traits separated by commas (e.g., "kind, intelligent, curious")',
            'rows': 3,
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        }),
        help_text="Enter traits that define your character's personality."
    )
    
    class Meta:
        model = Character
        fields = ['name', 'description', 'avatar', 'background_story', 'voice']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter character name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Give a brief description of your character',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'background_story': forms.Textarea(attrs={
                'placeholder': 'Share your character\'s backstory (optional)',
                'rows': 5,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'voice': forms.Textarea(attrs={
                'placeholder': 'Describe how your character speaks (optional)',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }
    
    def clean_traits_input(self):
        """Process the traits input into a list"""
        traits_text = self.cleaned_data.get('traits_input', '')
        
        if not traits_text:
            return []
        
        # Split by commas and strip whitespace
        traits = [trait.strip() for trait in traits_text.split(',')]
        
        # Remove empty traits
        traits = [trait for trait in traits if trait]
        
        return traits
    
    def save(self, commit=True):
        """Override save to handle the traits field"""
        instance = super().save(commit=False)
        
        # Set traits from the processed traits_input
        instance.traits = self.cleaned_data.get('traits_input', [])
        
        if commit:
            instance.save()
        
        return instance


class CharacterGenerationForm(forms.Form):
    """Form for AI-assisted character generation"""
    
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter character name',
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        }),
        help_text="Your character's name."
    )
    
    concept = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe your character concept (e.g., "A time-traveling detective from Victorian London" or "A friendly AI that lives in a smart home")',
            'rows': 3,
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        }),
        help_text="Provide a brief concept for your character."
    )
    
    traits = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter character traits separated by commas (e.g., "kind, intelligent, curious")',
            'rows': 2,
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        }),
        help_text="Optional traits to influence your character's personality."
    )
    
    additional_info = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Any additional information you\'d like to include (e.g., historical period, fictional universe, relationships, etc.)',
            'rows': 3,
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        }),
        help_text="Optional additional details to consider when generating your character."
    )
    
    def clean_traits(self):
        """Process the traits input into a list"""
        traits_text = self.cleaned_data.get('traits', '')
        
        if not traits_text:
            return []
        
        # Split by commas and strip whitespace
        traits = [trait.strip() for trait in traits_text.split(',')]
        
        # Remove empty traits
        traits = [trait for trait in traits if trait]
        
        return traits