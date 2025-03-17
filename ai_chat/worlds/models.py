from django.db import models
from django.conf import settings
from django.utils import timezone
from characters.models import Character

class World(models.Model):
    """Model for worldbuilding"""
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worlds')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Brief description of the world")
    
    # World details
    genre = models.CharField(max_length=100, blank=True)
    time_period = models.CharField(max_length=100, blank=True)
    rules = models.JSONField(default=dict, blank=True, help_text="Rules of the world as JSON")
    
    # Token usage tracking
    token_usage = models.IntegerField(default=0, help_text="Total tokens used for this world")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_archived = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
    
    def add_tokens(self, amount):
        """Add tokens to the world's total"""
        self.token_usage += amount
        self.save(update_fields=['token_usage'])
    
    def get_locations(self):
        """Get all locations in this world"""
        return self.locations.filter(is_archived=False).order_by('name')
    
    def get_characters(self):
        """Get all characters associated with this world"""
        return Character.objects.filter(
            worldlocationcharacter__location__world=self,
            is_archived=False
        ).distinct()


class WorldLocation(models.Model):
    """Model for locations within a world"""
    
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Description of the location")
    
    # Optional parent location (for hierarchical locations)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # Location details
    location_type = models.CharField(max_length=100, blank=True, help_text="Type of location (e.g., city, forest, building)")
    coordinates = models.CharField(max_length=100, blank=True, help_text="Coordinates on the world map")
    details = models.JSONField(default=dict, blank=True, help_text="Additional details as JSON")
    
    # Status
    is_archived = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.world.name})"
    
    def get_characters(self):
        """Get characters associated with this location"""
        return Character.objects.filter(worldlocationcharacter__location=self, is_archived=False)


class WorldLocationCharacter(models.Model):
    """Model for character associations with world locations"""
    
    location = models.ForeignKey(WorldLocation, on_delete=models.CASCADE, related_name='character_associations')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='location_associations')
    
    # Association details
    ASSOCIATION_TYPES = (
        ('resident', 'Resident'),
        ('visitor', 'Visitor'),
        ('ruler', 'Ruler'),
        ('worker', 'Worker'),
        ('imprisoned', 'Imprisoned'),
        ('historical', 'Historical Connection'),
        ('other', 'Other'),
    )
    association_type = models.CharField(max_length=20, choices=ASSOCIATION_TYPES, default='resident')
    
    notes = models.TextField(blank=True, help_text="Notes about the character's association with this location")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['location', 'character']
    
    def __str__(self):
        return f"{self.character.name} - {self.location.name} ({self.get_association_type_display()})"


class WorldFaction(models.Model):
    """Model for factions within a world"""
    
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='factions')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Description of the faction")
    
    # Faction details
    faction_type = models.CharField(max_length=100, blank=True, help_text="Type of faction (e.g., government, guild, religion)")
    
    # Optional headquarters location
    headquarters = models.ForeignKey(
        WorldLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headquartered_factions'
    )
    
    # Additional details
    leader = models.CharField(max_length=200, blank=True, help_text="Name of the faction leader")
    goals = models.TextField(blank=True, help_text="Goals and motivations of the faction")
    details = models.JSONField(default=dict, blank=True, help_text="Additional details as JSON")
    
    # Status
    is_archived = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.world.name})"
    
    def get_members(self):
        """Get characters who are members of this faction"""
        return Character.objects.filter(factionmember__faction=self, is_archived=False)


class FactionMember(models.Model):
    """Model for character memberships in factions"""
    
    faction = models.ForeignKey(WorldFaction, on_delete=models.CASCADE, related_name='members')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='faction_memberships')
    
    # Membership details
    ROLE_TYPES = (
        ('leader', 'Leader'),
        ('officer', 'Officer'),
        ('member', 'Member'),
        ('recruit', 'Recruit'),
        ('ally', 'Ally'),
        ('spy', 'Spy'),
        ('former', 'Former Member'),
        ('other', 'Other'),
    )
    role = models.CharField(max_length=20, choices=ROLE_TYPES, default='member')
    
    notes = models.TextField(blank=True, help_text="Notes about the character's role in this faction")
    
    # Timestamps
    joined_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['faction', 'character']
    
    def __str__(self):
        return f"{self.character.name} - {self.faction.name} ({self.get_role_display()})"


class WorldEvent(models.Model):
    """Model for historical events within a world"""
    
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Description of the event")
    
    # Event details
    event_type = models.CharField(max_length=100, blank=True, help_text="Type of event (e.g., war, coronation, disaster)")
    
    # Timing
    start_date = models.CharField(max_length=100, blank=True, help_text="When the event started (in-world date)")
    end_date = models.CharField(max_length=100, blank=True, help_text="When the event ended (in-world date)")
    
    # Location
    location = models.ForeignKey(
        WorldLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    
    # Significance
    significance = models.TextField(blank=True, help_text="Significance and impact of the event")
    
    # Additional details
    details = models.JSONField(default=dict, blank=True, help_text="Additional details as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.world.name})"


class WorldItem(models.Model):
    """Model for significant items within a world"""
    
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Description of the item")
    
    # Item details
    item_type = models.CharField(max_length=100, blank=True, help_text="Type of item (e.g., weapon, artifact, book)")
    
    # Location
    location = models.ForeignKey(
        WorldLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    
    # Owner
    character = models.ForeignKey(
        Character,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_items'
    )
    
    # Properties
    properties = models.TextField(blank=True, help_text="Special properties of the item")
    history = models.TextField(blank=True, help_text="Historical significance of the item")
    details = models.JSONField(default=dict, blank=True, help_text="Additional details as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.world.name})"


class WorldCulture(models.Model):
    """Model for cultures within a world"""
    
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='cultures')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Description of the culture")
    
    # Culture details
    values = models.TextField(blank=True, help_text="Core values of the culture")
    traditions = models.TextField(blank=True, help_text="Important traditions and customs")
    language = models.CharField(max_length=100, blank=True, help_text="Primary language")
    religion = models.TextField(blank=True, help_text="Religious beliefs")
    
    # Geographic spread
    locations = models.ManyToManyField(WorldLocation, related_name='cultures', blank=True)
    
    # Additional details
    notable_figures = models.TextField(blank=True, help_text="Important figures in this culture")
    details = models.JSONField(default=dict, blank=True, help_text="Additional details as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.world.name})"


class WorldNotes(models.Model):
    """Model for miscellaneous notes about a world"""
    
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    
    # Note type
    NOTE_TYPES = (
        ('general', 'General Note'),
        ('lore', 'Lore'),
        ('technology', 'Technology'),
        ('magic', 'Magic System'),
        ('creatures', 'Creatures'),
        ('politics', 'Politics'),
        ('economy', 'Economy'),
        ('religion', 'Religion'),
        ('other', 'Other'),
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
        verbose_name_plural = "World Notes"
    
    def __str__(self):
        return f"{self.title} ({self.world.name})"