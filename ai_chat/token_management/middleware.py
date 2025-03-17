from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from token_management.models import TokenAlert, TokenUsage, UserTokenLimit


class TokenUsageMiddleware:
    """Middleware to track and enforce token usage limits"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        if request.user.is_authenticated:
            # Check if the user has reached their token limit
            if self._check_token_limits(request.user):
                # User has reached their limit
                if not self._is_exempt_url(request.path):
                    messages.error(request, "You have reached your monthly token limit. Please upgrade your subscription or purchase additional tokens.")
                    return redirect(reverse('token_management:limit_reached'))
        
        # Process response
        response = self.get_response(request)
        return response
    
    def _check_token_limits(self, user):
        """
        Check if the user has reached their token limit
        Returns True if limit reached, False otherwise
        """
        # Check if user has unlimited tokens (e.g., staff)
        if user.is_staff:
            return False
        
        # Get the user's token limit object
        try:
            token_limit_obj = UserTokenLimit.objects.get(user=user)
        except UserTokenLimit.DoesNotExist:
            # Create a default limit if it doesn't exist
            token_limit_obj = UserTokenLimit.objects.create(user=user)
            return False  # New user, not at limit yet
        
        # Check if user is at their limit
        if token_limit_obj.token_usage_this_month >= token_limit_obj.monthly_limit:
            # Create 100% alert if it doesn't exist
            month = timezone.now().month
            year = timezone.now().year
            
            TokenAlert.objects.get_or_create(
                user=user,
                threshold=100,
                month=month,
                year=year,
                defaults={
                    'usage_at_alert': token_limit_obj.token_usage_this_month,
                    'limit_at_alert': token_limit_obj.monthly_limit
                }
            )
            return True
        
        # Create alerts at various thresholds
        for threshold in [50, 80, 95]:
            if token_limit_obj.token_usage_this_month >= (token_limit_obj.monthly_limit * threshold / 100):
                month = timezone.now().month
                year = timezone.now().year
                
                TokenAlert.objects.get_or_create(
                    user=user,
                    threshold=threshold,
                    month=month,
                    year=year,
                    defaults={
                        'usage_at_alert': token_limit_obj.token_usage_this_month,
                        'limit_at_alert': token_limit_obj.monthly_limit
                    }
                )
        
        return False
    
    def _is_exempt_url(self, path):
        """Check if the current URL is exempt from token limit enforcement"""
        exempt_paths = [
            '/token-management/limit-reached',
            '/token-management/purchase',
            '/users/subscription',
            '/admin/',
            '/logout/',
            '/static/',
            '/media/',
            '/accounts/',
        ]
        
        return any(path.startswith(exempt) for exempt in exempt_paths)


class TokenTrackingContextMiddleware:
    """Middleware to add token usage data to the request context"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request - add token tracking context
        if request.user.is_authenticated:
            try:
                token_limit_obj = UserTokenLimit.objects.get(user=request.user)
                token_limit = token_limit_obj.monthly_limit
            except UserTokenLimit.DoesNotExist:
                token_limit_obj = UserTokenLimit.objects.create(user=request.user, monthly_limit=50000)
                token_limit = token_limit_obj.monthly_limit
                
            # Calculate token usage
            from django.utils import timezone
            from django.db import models
            current_month = timezone.now().month
            current_year = timezone.now().year
            token_usage = TokenUsage.objects.filter(
                user=request.user,
                timestamp__month=current_month,
                timestamp__year=current_year
            ).values('tokens_used').aggregate(total=models.Sum('tokens_used'))['total'] or 0
            
            # Calculate percentage
            percent_used = (token_usage / token_limit) * 100 if token_limit > 0 else 0
            
            request.token_context = {
                'token_usage': token_usage,
                'token_limit': token_limit,
                'token_percent': percent_used,
                'token_alerts': request.user.token_alerts.filter(is_acknowledged=False).order_by('-created_at')
            }
        
        # Process response
        response = self.get_response(request)
        return response