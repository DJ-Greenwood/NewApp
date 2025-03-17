from django.db import models
from django.conf import settings
from django.utils import timezone
from characters.models import Character

class Journal(models.Model):
    """Model for user journals, which can include character interactions"""
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Brief description of the journal")
    
    # Journal type
    JOURNAL_TYPES = (
        ('personal', 'Personal Journal'),
        ('character', 'Character Journal'),
        ('project', 'Project Journal'),
        ('worldbuilding', 'Worldbuilding Journal'),
        ('dream', 'Dream Journal'),
        ('other', 'Other'),
    )
    journal_type = models.CharField(max_length=20, choices=JOURNAL_TYPES, default='personal')
    
    # Associated character (if it's a character journal)
    character = models.ForeignKey(
        Character, 
        on_delete=models.SET_NULL, 
        related_name='journals', 
        null=True, 
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title
    
    def entry_count(self):
        """Get the number of entries in this journal"""
        return self.entries.count()


class JournalEntry(models.Model):
    """Model for individual entries in a journal"""
    
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Entry date (can be different from created_at if recording past events)
    entry_date = models.DateField(default=timezone.now)
    
    # Optional metadata
    mood = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for this entry")
    
    # Characters mentioned in this entry
    characters = models.ManyToManyField(Character, related_name='journal_entries', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-entry_date', '-created_at']
        verbose_name_plural = "Journal entries"
    
    def __str__(self):
        return f"{self.journal.title} - {self.title} ({self.entry_date.strftime('%Y-%m-%d')})"
    
    def word_count(self):
        """Count the number of words in the entry"""
        return len(self.content.split())


class JournalTemplate(models.Model):
    """Model for journal entry templates"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journal_templates')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Template content with placeholders")
    
    # Template type
    TEMPLATE_TYPES = (
        ('daily', 'Daily Reflection'),
        ('gratitude', 'Gratitude Journal'),
        ('goal', 'Goal Setting'),
        ('character', 'Character Exploration'),
        ('dream', 'Dream Log'),
        ('project', 'Project Update'),
        ('custom', 'Custom Template'),
    )
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='custom')
    
    # Is this a system template or user-created?
    is_system = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return self.title


class JournalPrompt(models.Model):
    """Model for journal writing prompts"""
    
    # Prompt text
    text = models.TextField()
    
    # Prompt category
    PROMPT_CATEGORIES = (
        ('reflection', 'Self-Reflection'),
        ('creative', 'Creative Writing'),
        ('character', 'Character Development'),
        ('worldbuilding', 'Worldbuilding'),
        ('goal', 'Goal Setting'),
        ('gratitude', 'Gratitude'),
        ('general', 'General'),
    )
    category = models.CharField(max_length=20, choices=PROMPT_CATEGORIES, default='general')
    
    # Is this a system prompt or user-created?
    is_system = models.BooleanField(default=True)
    
    # Creator (if user-created)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='journal_prompts',
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.text[:50] + ('...' if len(self.text) > 50 else '')