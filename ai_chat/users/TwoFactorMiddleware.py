from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class TwoFactorMiddleware:
    """
    Middleware to check if a user has 2FA enabled and has verified their session.
    If 2FA is enabled but not verified, redirect to the 2FA verification page.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        user = request.user
        
        # Paths that are exempt from 2FA check
        exempt_paths = [
            reverse('users:verify_2fa'),
            reverse('users:login'),
            reverse('users:logout'),
            # Add other public paths here
        ]
        
        # Skip checks for anonymous users or exempt paths
        if not user.is_authenticated or request.path in exempt_paths or request.path.startswith('/static/'):
            return self.get_response(request)
        
        # Check if 2FA is enabled and not verified in this session
        if user.two_factor_enabled and not request.session.get('2fa_verified', False):
            # Store the originally requested URL to redirect back after verification
            request.session['next_url'] = request.get_full_path()
            
            # Redirect to 2FA verification
            return redirect(reverse('users:verify_2fa'))
        
        # Continue with the request
        return self.get_response(request)