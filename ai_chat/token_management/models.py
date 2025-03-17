# token_management/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

# Remove CustomUser import/definition - use settings.AUTH_USER_MODEL instead

class UserTokenLimit(models.Model):
    """Model for tracking user token limits and settings."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='token_limit'
    )
    monthly_limit = models.PositiveIntegerField(default=50000)  # Default limit for free tier
    alert_threshold = models.PositiveIntegerField(default=80)  # Default alert threshold in percentage
    
    # For calendar month reset
    current_usage = models.IntegerField(default=0)  # Token usage in current month
    last_reset = models.DateTimeField(default=timezone.now)  # Last time tokens were reset
    
    # For trial tracking
    is_trial = models.BooleanField(default=True)  # Whether user is in trial period
    trial_start = models.DateTimeField(default=timezone.now)  # When trial started
    trial_days = models.IntegerField(default=14)  # Length of trial in days
    has_seen_conversion = models.BooleanField(default=False)  # Whether user has seen conversion popup
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_trial']),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s token limit ({self.monthly_limit})"
    
    def get_token_percent_used(self):
        """Calculate percentage of token usage"""
        if self.monthly_limit == 0:
            return 0  # Avoid division by zero
        return min(100, (self.current_usage / self.monthly_limit) * 100)
    
    def check_and_reset_tokens(self):
        """Reset tokens if we're in a new month"""
        now = timezone.now()
        last_reset_month = self.last_reset.month
        last_reset_year = self.last_reset.year
        
        if now.month != last_reset_month or now.year != last_reset_year:
            # Create a historical record before resetting
            TokenHistory.objects.create(
                user=self.user,
                month=last_reset_month,
                year=last_reset_year,
                total_usage=self.current_usage,
                allocated_limit=self.monthly_limit
            )
            
            # Reset for the new month
            self.current_usage = 0
            self.last_reset = now
            self.save(update_fields=['current_usage', 'last_reset'])
            return True
        return False
    
    def days_until_next_month(self):
        """Calculate days until next month (token reset)"""
        now = timezone.now()
        # Get the first day of next month
        if now.month == 12:
            next_month = timezone.datetime(now.year + 1, 1, 1, tzinfo=now.tzinfo)
        else:
            next_month = timezone.datetime(now.year, now.month + 1, 1, tzinfo=now.tzinfo)
        
        # Calculate days remaining
        delta = next_month - now
        return delta.days
    
    def days_left_in_trial(self):
        """Calculate days remaining in trial period"""
        if not self.is_trial:
            return 0
            
        now = timezone.now()
        trial_end = self.trial_start + timezone.timedelta(days=self.trial_days)
        
        if now >= trial_end:
            return 0
            
        delta = trial_end - now
        return delta.days
    
    def should_show_conversion(self):
        """Determine if we should show trial conversion popup"""
        if not self.is_trial or self.has_seen_conversion:
            return False
            
        # Show popup when 3 days left in trial or less
        days_left = self.days_left_in_trial()
        return days_left <= 3
    
    def update_token_usage(self, amount, feature=None, **kwargs):
        """Update token usage with the specified amount"""
        with transaction.atomic():
            # Check if we need to reset for a new month
            self.check_and_reset_tokens()
            
            # Lock the row to prevent race conditions
            limit_obj = UserTokenLimit.objects.select_for_update().get(id=self.id)
            limit_obj.current_usage += amount
            limit_obj.save(update_fields=['current_usage'])
            
            # Add to usage history - this is already done in _log_token_usage, so we don't need it here
            # TokenUsage.objects.create(
            #     user=self.user,
            #     feature=feature or 'other',
            #     tokens_used=amount,
            #     **kwargs
            # )
            
            # Check for thresholds and create alerts if needed
            self._check_thresholds_and_create_alerts()
            
        return self.current_usage

    def _check_thresholds_and_create_alerts(self):
        """Check if user has crossed any token usage thresholds and create alerts"""
        # Skip if the user is staff (likely has unlimited tokens)
        if self.user.is_staff:
            return
            
        # Get current month and year
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        
        # Calculate percentage used
        percent_used = self.get_token_percent_used()
        
        # Check thresholds
        for threshold in [50, 80, 95, 100]:
            if percent_used >= threshold:
                # Try to create an alert (will be ignored if one already exists for this threshold/month)
                TokenAlert.objects.get_or_create(
                    user=self.user,
                    threshold=threshold,
                    month=current_month,
                    year=current_year,
                    defaults={
                        'usage_at_alert': self.current_usage,
                        'limit_at_alert': self.monthly_limit
                    }
                )

    def check_and_create_alerts(self):
        """Check if we need to create alerts for the user"""
        # Check if user is staff
        if self.user.is_staff:
            return
        
        # Check if we need to create alerts
        self._check_thresholds_and_create_alerts()
    
    def update_token_usage(self, amount, feature=None, **kwargs):
        """Update token usage with the specified amount"""
        with transaction.atomic():
            # Check if we need to reset for a new month
            self.check_and_reset_tokens()
            
            # Lock the row to prevent race conditions
            limit_obj = UserTokenLimit.objects.select_for_update().get(id=self.id)
            limit_obj.current_usage += amount
            limit_obj.save(update_fields=['current_usage'])
            
            # Add to usage history
            TokenUsage.objects.create(
                user=self.user,
                feature=feature or 'other',
                tokens_used=amount,
                **kwargs
            )
            
            # Check if we need to create alerts
            self.check_and_create_alerts()

class TokenUsage(models.Model):
    """Model to track token usage"""
    
    FEATURE_CHOICES = (
        ('character_creation', 'Character Creation'),
        ('character_chat', 'Character Chat'),
        ('story_assistance', 'Story Assistance'),
        ('memory_summarization', 'Memory Summarization'),
        ('world_building', 'World Building'),
        ('plot_development', 'Plot Development'),
        ('character_development', 'Character Development'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='token_usages'
    )
    feature = models.CharField(max_length=30, choices=FEATURE_CHOICES)
    tokens_used = models.IntegerField()
    
    # Optional references to relate the usage to specific objects
    character_id = models.IntegerField(null=True, blank=True)
    conversation_id = models.IntegerField(null=True, blank=True)
    story_id = models.IntegerField(null=True, blank=True)
    world_id = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['feature']),
        ]
    
    def __str__(self):
        return f"{self.user.username} used {self.tokens_used} tokens for {self.feature}"
    
    @classmethod
    def get_usage_summary(cls, user):
        """Get a summary of token usage for a user"""
        # Get the current billing period
        today = timezone.now().date()
        month_start = today.replace(day=1)
        next_month = (today.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
        
        # Get usage for the current billing period
        period_usage = cls.objects.filter(
            user=user,
            timestamp__date__gte=month_start,
            timestamp__date__lt=next_month
        )
        
        # Overall usage for the period
        total_usage = period_usage.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
        
        # Usage by feature
        feature_usage = {}
        for feature_choice in cls.FEATURE_CHOICES:
            feature_code = feature_choice[0]
            feature_usage[feature_code] = period_usage.filter(
                feature=feature_code
            ).aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
        
        return {
            'total': total_usage,
            'by_feature': feature_usage,
            'period_start': month_start,
            'period_end': next_month - timezone.timedelta(days=1),
        }

class TokenAlert(models.Model):
    """Model to track token usage alerts sent to users"""
    
    THRESHOLD_CHOICES = (
        (50, '50% of limit'),
        (80, '80% of limit'),
        (95, '95% of limit'),
        (100, '100% of limit (limit reached)'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='token_alerts'
    )
    threshold = models.IntegerField(choices=THRESHOLD_CHOICES)
    is_acknowledged = models.BooleanField(default=False)
    
    # The actual token usage and limit at the time of the alert
    usage_at_alert = models.IntegerField()
    limit_at_alert = models.IntegerField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Month and year for the alert (for unique constraint)
    month = models.IntegerField(editable=False)
    year = models.IntegerField(editable=False)

    class Meta:
        ordering = ['-created_at']
        # Ensure we don't create duplicate alerts for the same threshold in the same period
        unique_together = ['user', 'threshold', 'month', 'year']
    
    def acknowledge(self):
        """Mark the alert as acknowledged"""
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['is_acknowledged', 'acknowledged_at'])
    
    def __str__(self):
        return f"Alert for {self.user.username}: {self.threshold}% at {self.created_at.strftime('%Y-%m-%d')}"

@receiver(pre_save, sender=TokenAlert)
def set_month_year(sender, instance, **kwargs):
    if not instance.pk:  # Only on creation
        instance.month = instance.created_at.month if instance.created_at else timezone.now().month
        instance.year = instance.created_at.year if instance.created_at else timezone.now().year

class TokenPurchase(models.Model):
    """Model to track token purchases"""
    
    # Unique transaction ID
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='token_purchases'
    )
    tokens_purchased = models.IntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Payment processing details
    payment_provider = models.CharField(max_length=20, default='stripe')
    payment_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(
        max_length=20, 
        default='pending',
        choices=(
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        )
    )
    
    # Idempotency key to prevent duplicate transactions
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Add a lock field for transaction processing
    is_processing = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'payment_status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['idempotency_key']),
        ]
    
    def __str__(self):
        return f"{self.user.username} purchased {self.tokens_purchased} tokens for {self.amount_paid} {self.currency}"
    
    def clean(self):
        # Check if there's already a processing transaction for this user
        if self.is_processing:
            existing_processing = TokenPurchase.objects.filter(
                user=self.user, 
                is_processing=True
            ).exclude(pk=self.pk).exists()
            
            if existing_processing:
                raise ValidationError("Another transaction is currently processing for this user.")
    
    @transaction.atomic
    def mark_completed(self):
        """Mark the purchase as completed and add tokens to user account"""
        # Lock this record to prevent race conditions
        purchase = TokenPurchase.objects.select_for_update().get(pk=self.pk)
        
        if purchase.payment_status not in ['completed', 'refunded']:
            purchase.payment_status = 'completed'
            purchase.completed_at = timezone.now()
            purchase.is_processing = False
            purchase.save(update_fields=['payment_status', 'completed_at', 'is_processing'])
            
            # Add the tokens to the user's account
            try:
                token_limit = UserTokenLimit.objects.select_for_update().get(user=self.user)
                token_limit.monthly_limit += self.tokens_purchased
                token_limit.save()
            except UserTokenLimit.DoesNotExist:
                UserTokenLimit.objects.create(
                    user=self.user,
                    monthly_limit=self.tokens_purchased
                )
            
            return True
        return False

# Signal to create UserTokenLimit for new users
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_token_limit(sender, instance, created, **kwargs):
    if created:
        # Set default limit based on subscription tier
        default_limit = 50000  # Default for free tier
        
        if hasattr(instance, 'subscription_tier'):
            if instance.subscription_tier == 'basic':
                default_limit = 100000
            elif instance.subscription_tier == 'enterprise':
                default_limit = 500000
        
        UserTokenLimit.objects.create(
            user=instance,
            monthly_limit=default_limit
        )

class TokenHistory(models.Model):
    """Model for tracking historical token usage by month"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='token_history'
    )
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    total_usage = models.IntegerField()
    allocated_limit = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['user', 'month', 'year']
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s usage for {self.month}/{self.year}: {self.total_usage}/{self.allocated_limit}"
    
    def get_percent_used(self):
        """Calculate percentage of token usage"""
        if self.allocated_limit == 0:
            return 0
        return min(100, (self.total_usage / self.allocated_limit) * 100)
    
    @classmethod
    def get_yearly_summary(cls, user, year):
        """Get monthly usage summary for a specific year"""
        return cls.objects.filter(user=user, year=year).order_by('month')
    