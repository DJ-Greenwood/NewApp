from .models import UserTokenLimit
from django.utils import timezone

def token_usage(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        # Get token limit from UserTokenLimit model
        try:
            token_limit_obj = UserTokenLimit.objects.get(user=request.user)
            # Check if tokens need to be reset for a new month
            token_limit_obj.check_and_reset_tokens()
            
            token_limit = token_limit_obj.monthly_limit
            token_usage = token_limit_obj.current_usage
            token_percent = token_limit_obj.get_token_percent_used()
            days_until_reset = token_limit_obj.days_until_next_month()
            
            # Trial information
            is_trial = token_limit_obj.is_trial
            trial_days_left = token_limit_obj.days_left_in_trial()
            show_conversion = token_limit_obj.should_show_conversion()
            
        except UserTokenLimit.DoesNotExist:
            # Create a default token limit if it doesn't exist
            token_limit_obj = UserTokenLimit.objects.create(
                user=request.user, 
                monthly_limit=50000,
                is_trial=True,
                trial_start=timezone.now()
            )
            
            token_limit = token_limit_obj.monthly_limit
            token_usage = 0
            token_percent = 0
            days_until_reset = token_limit_obj.days_until_next_month()
            
            # Trial information
            is_trial = True
            trial_days_left = 14
            show_conversion = False
            
        return {
            'token_usage': token_usage,
            'token_limit': token_limit,
            'token_percent': token_percent,
            'days_until_reset': days_until_reset,
            'token_alerts': request.user.token_alerts.filter(is_acknowledged=False).count(),
            'is_trial': is_trial,
            'trial_days_left': trial_days_left,
            'show_conversion': show_conversion,
        }
    return {}