from django.db import models
from django.conf import settings
from django.utils import timezone
from characters.models import Character

class Conversation(models.Model):
    """Model for conversations with characters"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, blank=True)
    
    # Conversation context
    context = models.TextField(blank=True, help_text="Optional context for the conversation")
    
    # Token usage tracking
    total_tokens = models.IntegerField(default=0, help_text="Total tokens used in this conversation")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_archived = models.BooleanField(default=False)

    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title or 'Conversation'} with {self.character.name}"
    
    def add_tokens(self, amount):
        """Add tokens to the conversation total"""
        self.total_tokens += amount
        self.save(update_fields=['total_tokens'])
    
    def get_recent_messages(self, limit=10):
        """Get the most recent messages in this conversation"""
        return self.messages.order_by('-timestamp')[:limit]
    
    def mark_as_read(self):
        """Mark all unread messages in the conversation as read"""
        self.messages.filter(is_read=False, sender='character').update(is_read=True)


class Message(models.Model):
    """Model for individual messages in a conversation"""
    
    SENDER_CHOICES = (
        ('user', 'User'),
        ('character', 'Character'),
        ('system', 'System'),
    )
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    
    # Message metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the message")
    
    # Token usage tracking
    prompt_tokens = models.IntegerField(default=0, help_text="Tokens used in the prompt")
    completion_tokens = models.IntegerField(default=0, help_text="Tokens used in the completion")
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Status
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def total_tokens(self):
        """Calculate total tokens used by this message"""
        return self.prompt_tokens + self.completion_tokens


class ConversationSummary(models.Model):
    """Model for storing summaries of conversation segments"""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='summaries')
    content = models.TextField(help_text="Summarized content")
    start_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, related_name='+')
    end_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, related_name='+')
    
    # Token usage tracking
    token_count = models.IntegerField(default=0, help_text="Tokens in this summary")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Summary for {self.conversation} ({self.created_at.strftime('%Y-%m-%d')})"