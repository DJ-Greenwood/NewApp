from django import forms
from .models import (
    World, WorldLocation, WorldLocationCharacter, WorldFaction, FactionMember,
    WorldEvent, WorldItem, WorldCulture, WorldNotes
)

class WorldForm(forms.ModelForm):
    """Form for creating and editing worlds"""
    
    class Meta:
        model = World
        fields = ['name', 'description', 'genre', 'time_period', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter world name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Provide a brief description of your world',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'genre': forms.TextInput(attrs={
                'placeholder': 'E.g., Fantasy, Sci-Fi, Historical',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'time_period': forms.TextInput(attrs={
                'placeholder': 'E.g., Medieval, Future, Victorian Era',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber focus:ring-amber'
            }),
        }
        help_texts = {
            'is_public': 'Make this world visible to other users (coming soon)'
        }


class LocationForm(forms.ModelForm):
    """Form for creating and editing locations"""
    
    class Meta:
        model = WorldLocation
        fields = ['name', 'description', 'parent', 'location_type', 'coordinates']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter location name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe this location',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'parent': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'location_type': forms.TextInput(attrs={
                'placeholder': 'E.g., city, forest, building',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'coordinates': forms.TextInput(attrs={
                'placeholder': 'Optional coordinates',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class LocationCharacterForm(forms.Form):
    """Form for adding a character to a location"""
    
    character = forms.ModelChoiceField(
        queryset=None,  # Will be set in the view
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )
    
    association_type = forms.ChoiceField(
        choices=WorldLocationCharacter.ASSOCIATION_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Optional notes about why this character is associated with this location',
            'rows': 3,
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )


class FactionForm(forms.ModelForm):
    """Form for creating and editing factions"""
    
    class Meta:
        model = WorldFaction
        fields = ['name', 'description', 'faction_type', 'headquarters', 'leader', 'goals']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter faction name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe this faction',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'faction_type': forms.TextInput(attrs={
                'placeholder': 'E.g., government, guild, religion',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'headquarters': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'leader': forms.TextInput(attrs={
                'placeholder': 'Name of faction leader (if any)',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'goals': forms.Textarea(attrs={
                'placeholder': 'What are this faction\'s goals and motivations?',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class FactionMemberForm(forms.Form):
    """Form for adding a character as a faction member"""
    
    character = forms.ModelChoiceField(
        queryset=None,  # Will be set in the view
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )
    
    role = forms.ChoiceField(
        choices=FactionMember.ROLE_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Optional notes about this character\'s role in the faction',
            'rows': 3,
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )
    
    joined_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
        })
    )


class EventForm(forms.ModelForm):
    """Form for creating and editing events"""
    
    class Meta:
        model = WorldEvent
        fields = ['name', 'description', 'event_type', 'start_date', 'end_date', 'location', 'significance']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter event name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe this event',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'event_type': forms.TextInput(attrs={
                'placeholder': 'E.g., war, coronation, disaster',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'start_date': forms.TextInput(attrs={
                'placeholder': 'When the event started (in-world date)',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'end_date': forms.TextInput(attrs={
                'placeholder': 'When the event ended (in-world date)',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'significance': forms.Textarea(attrs={
                'placeholder': 'What was the impact and significance of this event?',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class ItemForm(forms.ModelForm):
    """Form for creating and editing items"""
    
    class Meta:
        model = WorldItem
        fields = ['name', 'description', 'item_type', 'location', 'character', 'properties', 'history']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter item name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe this item',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'item_type': forms.TextInput(attrs={
                'placeholder': 'E.g., weapon, artifact, book',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'character': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'properties': forms.Textarea(attrs={
                'placeholder': 'What special properties does this item have?',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'history': forms.Textarea(attrs={
                'placeholder': 'What is the history of this item?',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class CultureForm(forms.ModelForm):
    """Form for creating and editing cultures"""
    
    class Meta:
        model = WorldCulture
        fields = ['name', 'description', 'values', 'traditions', 'language', 'religion', 'locations', 'notable_figures']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter culture name',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe this culture',
                'rows': 3,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'values': forms.Textarea(attrs={
                'placeholder': 'What does this culture value?',
                'rows': 2,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'traditions': forms.Textarea(attrs={
                'placeholder': 'What traditions do they observe?',
                'rows': 2,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'language': forms.TextInput(attrs={
                'placeholder': 'What language(s) do they speak?',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'religion': forms.Textarea(attrs={
                'placeholder': 'What are their religious beliefs?',
                'rows': 2,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'locations': forms.SelectMultiple(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'notable_figures': forms.Textarea(attrs={
                'placeholder': 'Who are important figures in this culture?',
                'rows': 2,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }


class NotesForm(forms.ModelForm):
    """Form for creating and editing world notes"""
    
    class Meta:
        model = WorldNotes
        fields = ['title', 'content', 'note_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter note title',
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your note here',
                'rows': 8,
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
            'note_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:border-amber focus:ring focus:ring-amber focus:ring-opacity-50'
            }),
        }