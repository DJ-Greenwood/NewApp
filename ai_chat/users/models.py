# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Subscription fields
    SUBSCRIPTION_TIERS = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('enterprise', 'Enterprise'),
    )
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='free')
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    
    # Settings and preferences
    preferences = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return self.username
        
    # Property methods to maintain compatibility with old code
    @property
    def token_usage_this_month(self):
        """
        Backward compatibility property to get token usage from the token limit model
        """
        try:
            return self.token_limit.token_usage_this_month
        except (AttributeError, Exception):
            return 0
            
    @property
    def token_reset_date(self):
        """
        Backward compatibility property to get token reset date from the token limit model
        """
        try:
            return self.token_limit.token_reset_date
        except (AttributeError, Exception):
            return None
            
    @property
    def token_limit(self):
        """
        Backward compatibility property for token limit
        """
        try:
            from token_management.models import UserTokenLimit
            return UserTokenLimit.objects.get(user=self).monthly_limit
        except Exception:
            return 0
            
    def get_token_percent_used(self):
        """
        Backward compatibility method to calculate percentage of token usage
        """
        try:
            return self.token_limit.get_token_percent_used()
        except (AttributeError, Exception):
            return 0