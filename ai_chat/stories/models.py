from django.db import models
from django.conf import settings
from django.utils import timezone
from characters.models import Character

class Story(models.Model):
    """Model for stories written by users with character collaboration"""
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Brief description of the story")
    
    # Content
    content = models.TextField(blank=True, help_text="The story content")
    
    # Story metadata
    genre = models.CharField(max_length=100, blank=True)
    is_complete = models.BooleanField(default=False)
    
    # Characters involved in the story
    characters = models.ManyToManyField(Character, related_name='stories', blank=True)
    
    # Token usage tracking
    token_usage = models.IntegerField(default=0, help_text="Total tokens used in this story")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_archived = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = "Stories"
    
    def __str__(self):
        return self.title
    
    def add_tokens(self, amount):
        """Add tokens to the story's total"""
        self.token_usage += amount
        self.save(update_fields=['token_usage'])
    
    def word_count(self):
        """Count the number of words in the story"""
        return len(self.content.split())


class Chapter(models.Model):
    """Model for individual chapters in a story"""
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="Order of chapter in the story")
    
    # Characters featured in this chapter
    characters = models.ManyToManyField(Character, related_name='chapters', blank=True)
    
    # Token usage tracking
    token_usage = models.IntegerField(default=0, help_text="Tokens used in this chapter")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.story.title} - {self.title}"
    
    def word_count(self):
        """Count the number of words in the chapter"""
        return len(self.content.split())


class StoryNote(models.Model):
    """Model for notes and outlines related to a story"""
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    
    # Note type
    NOTE_TYPES = (
        ('outline', 'Outline'),
        ('character_note', 'Character Note'),
        ('worldbuilding', 'Worldbuilding'),
        ('plot_idea', 'Plot Idea'),
        ('research', 'Research'),
        ('general', 'General Note'),
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    
    # Character relevance
    character = models.ForeignKey(
        Character, 
        on_delete=models.SET_NULL, 
        related_name='story_notes', 
        null=True, 
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.story.title} - {self.title}"


class StoryAssistance(models.Model):
    """Model for AI story-writing assistance logs"""
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='assistance_logs')
    
    # Assistance type
    ASSISTANCE_TYPES = (
        ('plot_suggestion', 'Plot Suggestion'),
        ('character_dialogue', 'Character Dialogue'),
        ('description', 'Description Enhancement'),
        ('continuation', 'Story Continuation'),
        ('editing', 'Editing and Revision'),
        ('worldbuilding', 'Worldbuilding Detail'),
    )
    assistance_type = models.CharField(max_length=30, choices=ASSISTANCE_TYPES)
    
    # Prompt and response
    user_prompt = models.TextField(help_text="User's request for assistance")
    ai_response = models.TextField(help_text="AI-generated assistance")
    
    # Token usage tracking
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    
    # Was the suggestion used?
    was_used = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.story.title} - {self.assistance_type} assistance"
    
    @property
    def total_tokens(self):
        """Calculate total tokens used"""
        return self.prompt_tokens + self.completion_tokens