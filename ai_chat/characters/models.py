from django.db import models
from django.conf import settings
from django.utils import timezone

class Character(models.Model):
    """Model for AI characters"""
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='character_avatars/', blank=True, null=True)
    description = models.TextField(help_text="Brief description of the character")
    
    # Detailed traits and personality
    background_story = models.TextField(blank=True, help_text="Character's backstory")
    traits = models.JSONField(default=list, blank=True, help_text="List of character traits as JSON")
    personality_details = models.JSONField(default=dict, blank=True, help_text="Detailed personality aspects as JSON")
    voice = models.TextField(blank=True, help_text="Description of the character's voice and speech patterns")
    
    # Vector database reference
    vector_id = models.CharField(max_length=100, blank=True, help_text="Reference ID in the vector database")
    
    # Token usage tracking
    creation_token_cost = models.IntegerField(default=0, help_text="Tokens used during character creation")
    avg_interaction_tokens = models.FloatField(default=0, help_text="Average tokens per interaction")
    total_interactions = models.IntegerField(default=0, help_text="Number of interactions with this character")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_interaction = models.DateTimeField(blank=True, null=True)
    
    # Status
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-last_interaction', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def record_interaction(self, tokens_used):
        """Update interaction statistics"""
        now = timezone.now()
        # Calculate new average
        new_total = self.total_interactions + 1
        new_avg = ((self.avg_interaction_tokens * self.total_interactions) + tokens_used) / new_total
        
        # Update fields
        self.total_interactions = new_total
        self.avg_interaction_tokens = new_avg
        self.last_interaction = now
        self.save(update_fields=['total_interactions', 'avg_interaction_tokens', 'last_interaction'])
    
    def get_memory_objects(self):
        """Retrieve related memory objects from the character's memory"""
        return self.memories.filter(is_active=True).order_by('-importance_score')
    
    def get_traits_list(self):
        """Convert the JSON traits field to a Python list"""
        if isinstance(self.traits, list):
            return self.traits
        return []


class CharacterMemory(models.Model):
    """Memory objects related to a character"""
    
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='memories')
    content = models.TextField(help_text="The memory content")
    source = models.CharField(max_length=100, help_text="Where this memory came from (conversation, story, etc.)")
    
    # Vector database reference
    vector_id = models.CharField(max_length=100, blank=True, help_text="Reference ID in the vector database")
    embedding = models.JSONField(blank=True, null=True, help_text="Optional local storage of embedding vector")
    
    # Memory importance and retrieval
    importance_score = models.FloatField(default=0.5, help_text="How important this memory is (0-1)")
    is_active = models.BooleanField(default=True, help_text="Whether this memory is active in the character's memory")
    
    # Token usage
    token_count = models.IntegerField(default=0, help_text="Number of tokens in this memory")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Memory for {self.character.name}: {self.content[:30]}..."
    
    def access(self):
        """Mark this memory as accessed"""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])


class CharacterRelationship(models.Model):
    """Relationships between characters"""
    
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='relationships')
    related_character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='reverse_relationships')
    relationship_type = models.CharField(max_length=100, help_text="Type of relationship (friend, enemy, etc.)")
    description = models.TextField(blank=True, help_text="Description of the relationship")
    
    # Relationship strength and feelings
    strength = models.FloatField(default=0.5, help_text="Strength of relationship (0-1)")
    feelings = models.JSONField(default=dict, blank=True, help_text="Detailed feelings as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['character', 'related_character']
    
    def __str__(self):
        return f"{self.character.name}'s relationship with {self.related_character.name}"