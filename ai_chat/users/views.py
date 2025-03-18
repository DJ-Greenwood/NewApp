# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from .forms import CustomUserCreationForm, CustomUserChangeForm, UserPreferencesForm
from token_management.models import UserTokenLimit, TokenUsage
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, 
    PasswordResetCompleteView, PasswordChangeView, PasswordChangeDoneView
)
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            
            # Redirect to the next page if provided, otherwise to home
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'component/profile/login.html')

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('users:login')

@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    
    # Get token usage statistics
    token_settings, created = UserTokenLimit.objects.get_or_create(user=user)
    
    # Calculate token usage
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_usage = TokenUsage.objects.filter(
        user=user, 
        timestamp__month=current_month,
        timestamp__year=current_year
    ).aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
    
    total_usage = TokenUsage.objects.filter(user=user).aggregate(
        Sum('tokens_used')
    )['tokens_used__sum'] or 0
    
    token_usage = {
        'monthly_tokens_used': monthly_usage,
        'total_tokens_used': total_usage,
        'monthly_limit': token_settings.monthly_limit,
        'percent_used': (monthly_usage / token_settings.monthly_limit * 100) if token_settings.monthly_limit else 0
    }
    
    # Get other statistics
    conversation_count = 0  # Replace with actual query when model exists
    character_count = 0  # Replace with actual query when model exists
    most_active_character = None  # Replace with actual query when model exists
    
    context = {
        'user': user,
        'token_usage': token_usage,
        'conversation_count': conversation_count,
        'character_count': character_count,
        'most_active_character': most_active_character,
    }
    
    return render(request, 'components/profile/profile.html', context)


@login_required
def subscription_view(request):
    """Manage subscription tier"""
    user = request.user
    token_settings, created = UserTokenLimit.objects.get_or_create(user=user)
    
    # Get subscription tiers and current tier
    tiers = {
        'free': {
            'name': 'Free',
            'monthly_limit': 50000,
            'price': 0,
            'features': ['Basic character creation', 'Limited conversations', 'Standard AI model']
        },
        'basic': {
            'name': 'Basic',
            'monthly_limit': 200000,
            'price': 9.99,
            'features': ['Advanced character creation', 'Unlimited conversations', 'Access to GPT-4', 'Story creation']
        },
        'enterprise': {
            'name': 'Enterprise',
            'monthly_limit': 500000,
            'price': 29.99,
            'features': ['All features', 'Priority support', 'API access', 'Claude 3 Opus access', 'World building']
        }
    }
    
    current_tier = user.subscription_tier
    
    if request.method == 'POST':
        new_tier = request.POST.get('tier')
        if new_tier in tiers:
            # Update user's subscription tier
            user.subscription_tier = new_tier
            token_settings.monthly_limit = tiers[new_tier]['monthly_limit']
            
            # Set subscription dates
            now = timezone.now()
            user.subscription_start_date = now
            
            # Set end date 1 month in the future
            user.subscription_end_date = now.replace(
                month=now.month + 1 if now.month < 12 else 1,
                year=now.year if now.month < 12 else now.year + 1
            )
            
            user.save()
            token_settings.save()
            
            messages.success(request, f"Subscription updated to {tiers[new_tier]['name']} plan.")
            return redirect('users:profile')
    
    context = {
        'current_tier': current_tier,
        'tiers': tiers,
    }
    
    return render(request, 'component/profile/subscription.html', context)

def signup(request):
    """
    View for user registration/signup
    Handles the signup form submission, user creation,
    and initial token limit setup
    """
    # If the user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create the user account
            user = form.save()
            
            # Create token limit settings for the new user (Free tier by default)
            UserTokenLimit.objects.create(
                user=user,
                monthly_limit=50000  # Default free tier allocation
            )
            
            # Set up default preferences
            user.preferences = {
                'theme': 'light',
                'enable_animations': True,
                'compact_view': False,
                'default_ai_model': 'gpt-3.5-turbo',
                'default_temperature': 0.7,
                'default_max_tokens': 800,
                'auto_save_conversations': True,
                'enable_markdown': True,
                'enable_code_highlighting': True,
                'enable_message_timestamps': True,
                'email_notifications': False
            }
            user.save()
            
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            # Display success message
            messages.success(request, "Registration successful! Welcome to MyImaginaryFriends.ai!")
            
            # Redirect to the dashboard
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    # Get plan info from query parameters (for upgrade links from pricing page)
    initial_plan = request.GET.get('plan', 'free')
    
    return render(request, 'component/profile/signup.html', {
        'form': form,
        'initial_plan': initial_plan
    })

@login_required
@require_http_methods(["GET", "POST"])
def update_notifications(request):
    """
    View for handling the notification preferences page and form submission.
    GET: Renders the notification settings page
    POST: Updates the user's notification preferences
    """
    user = request.user
    
    if request.method == "POST":
        # Email notification settings
        user.email_notifications = 'email_notifications' in request.POST
        user.weekly_summary = 'weekly_summary' in request.POST
        user.marketing_emails = 'marketing_emails' in request.POST
        
        # Character notification settings
        user.character_responses = 'character_responses' in request.POST
        user.inactive_reminders = 'inactive_reminders' in request.POST
        user.character_birthdays = 'character_birthdays' in request.POST
        
        # Story notification settings
        user.story_updates = 'story_updates' in request.POST
        user.story_suggestions = 'story_suggestions' in request.POST
        
        # World notification settings
        user.world_updates = 'world_updates' in request.POST
        user.collaboration_invitations = 'collaboration_invitations' in request.POST
        
        # System notification settings
        user.token_alerts = 'token_alerts' in request.POST
        user.subscription_reminders = 'subscription_reminders' in request.POST
        user.feature_announcements = 'feature_announcements' in request.POST
        
        # Notification delivery methods
        user.delivery_email = 'delivery_email' in request.POST
        user.delivery_push = 'delivery_push' in request.POST
        user.delivery_sms = 'delivery_sms' in request.POST
        
        # If SMS delivery is enabled, update phone number
        if user.delivery_sms and 'phone_number' in request.POST:
            user.phone_number = request.POST.get('phone_number')
        
        # Notification frequency
        if 'notification_frequency' in request.POST:
            user.notification_frequency = request.POST.get('notification_frequency')
        
        # Quiet hours settings
        user.quiet_hours_enabled = 'quiet_hours_enabled' in request.POST
        
        if user.quiet_hours_enabled:
            user.quiet_hours_start = request.POST.get('quiet_hours_start')
            user.quiet_hours_end = request.POST.get('quiet_hours_end')
        
        # Save changes
        user.save()
        
        # Show success message
        messages.success(request, "Your notification preferences have been updated.")
        
        # Redirect to the profile page
        return redirect(reverse('users:profile'))
    
    # GET request - render the notifications settings page
    context = {
        'user': user,
    }
    
    return render(request, 'components/profile/update_notifications.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def update_privacy(request):
    """
    View for handling the privacy settings page and form submission.
    GET: Renders the privacy settings page
    POST: Updates the user's privacy settings
    """
    user = request.user
    
    if request.method == "POST":
        # Privacy settings
        user.public_profile = 'public_profile' in request.POST
        user.show_characters = 'show_characters' in request.POST
        user.show_stories = 'show_stories' in request.POST
        
        # Additional privacy settings can be added here
        
        # Save changes
        user.save()
        
        # Show success message
        messages.success(request, "Your privacy settings have been updated.")
        
        # Redirect to the profile page
        return redirect(reverse('users:profile'))
    
    # GET request - render the privacy settings page
    context = {
        'user': user,
    }
    
    return render(request, 'components/profile/update_privacy.html', context)

# In your users/views.py file
@login_required
def update_profile(request):
    """
    View for updating user profile information
    """
    user = request.user
    
    if request.method == "POST":
        # Process form data
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.bio = request.POST.get('bio', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
            
        # Save changes
        user.save()
        
        messages.success(request, "Your profile has been updated.")
        return redirect(reverse('users:profile'))
    
    # This view shouldn't be accessed directly via GET
    return redirect(reverse('users:profile'))

@login_required
def change_password(request):
    """
    View for changing user's password
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session to prevent the user from being logged out
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'component/profile/change_password.html', {'form': form})
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'component/profile/change_password.html', {'form': form})

import pyotp
import qrcode
import io
import base64
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings

@login_required
def setup_2fa(request):
    """
    View for setting up two-factor authentication
    """
    user = request.user
    
    # Check if 2FA is already enabled
    if user.two_factor_enabled:
        messages.error(request, "Two-factor authentication is already enabled for your account.")
        return redirect(reverse('users:profile'))
    
    # Generate a random secret key if not already present
    if not hasattr(user, 'two_factor_secret') or not user.two_factor_secret:
        # Generate a new secret key
        user.two_factor_secret = pyotp.random_base32()
        user.save()
    
    # Create an OTP URI for QR code generation
    totp = pyotp.TOTP(user.two_factor_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="MyImaginaryFriends.ai"
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    qr_code = f"data:image/png;base64,{img_str}"
    
    if request.method == 'POST':
        # Verify the authentication code
        verification_code = request.POST.get('verification_code')
        
        if not verification_code:
            messages.error(request, "Verification code is required.")
            return render(request, 'components/profile/setup_2fa.html', {'qr_code': qr_code, 'secret': user.two_factor_secret})
        
        # Verify the code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(verification_code):
            # Generate backup codes
            backup_codes = []
            for _ in range(10):  # Generate 10 backup codes
                backup_codes.append(pyotp.random_base32(length=8))
            
            # Save codes to user model (as a comma-separated string)
            user.two_factor_backup_codes = ','.join(backup_codes)
            user.two_factor_enabled = True
            user.save()
            
            messages.success(request, "Two-factor authentication has been successfully enabled for your account.")
            
            # Pass backup codes to the success template
            return render(request, 'components/profile/setup_2fa_success.html', {'backup_codes': backup_codes})
        else:
            messages.error(request, "Invalid verification code. Please try again.")
    
    return render(request, 'components/profile/setup_2fa.html', {'qr_code': qr_code, 'secret': user.two_factor_secret})


@login_required
def disable_2fa(request):
    """
    View for disabling two-factor authentication
    """
    user = request.user
    
    if not user.two_factor_enabled:
        messages.error(request, "Two-factor authentication is not enabled for your account.")
        return redirect(reverse('users:profile'))
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        
        if not verification_code:
            messages.error(request, "Verification code is required to disable 2FA.")
            return render(request, 'components/profile/disable_2fa.html')
        
        # Verify the code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(verification_code) or verification_code in user.two_factor_backup_codes.split(','):
            # Disable 2FA
            user.two_factor_enabled = False
            user.two_factor_secret = ""
            user.two_factor_backup_codes = ""
            user.save()
            
            messages.success(request, "Two-factor authentication has been disabled for your account.")
            return redirect(reverse('users:profile'))
        else:
            messages.error(request, "Invalid verification code. Please try again.")
    
    return render(request, 'components/profile/disable_2fa.html')

@login_required
def verify_2fa(request):
    """
    View for verifying 2FA during login
    """
    user = request.user
    
    # If 2FA is not enabled, redirect to home
    if not user.two_factor_enabled:
        return redirect(reverse('home'))
    
    # If 2FA is already verified in this session, redirect to the originally requested page
    if request.session.get('2fa_verified', False):
        next_url = request.session.get('next_url', reverse('home'))
        return redirect(next_url)
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        
        if not verification_code:
            messages.error(request, "Verification code is required.")
            return render(request, 'components/profile/verify_2fa.html')
        
        # Verify the code
        totp = pyotp.TOTP(user.two_factor_secret)
        backup_codes = user.two_factor_backup_codes.split(',') if user.two_factor_backup_codes else []
        
        if totp.verify(verification_code) or verification_code in backup_codes:
            # If it's a backup code, remove it from the list
            if verification_code in backup_codes:
                backup_codes.remove(verification_code)
                user.two_factor_backup_codes = ','.join(backup_codes)
                user.save()
            
            # Mark the session as 2FA verified
            request.session['2fa_verified'] = True
            
            # Redirect to the originally requested page or home
            next_url = request.session.get('next_url', reverse('home'))
            return redirect(next_url)
        else:
            messages.error(request, "Invalid verification code. Please try again.")
    
    return render(request, 'components/profile/verify_2fa.html')

import os
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import SuspiciousOperation

@login_required
def connect_google(request):
    """
    Initiates the OAuth flow to connect a Google account.
    """
    # Generate a state parameter to prevent CSRF
    state = os.urandom(16).hex()
    request.session['oauth_state'] = state
    
    # Store the return URL
    request.session['oauth_return_url'] = request.GET.get('next', reverse('users:profile'))
    
    # Build the OAuth authorization URL
    oauth_url = "https://accounts.google.com/o/oauth2/auth"
    redirect_uri = request.build_absolute_uri(reverse('users:google_callback'))
    
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'email profile',
        'state': state,
        'prompt': 'consent',  # Force Google to show consent screen
        'access_type': 'offline',  # Needed if we want a refresh token
    }
    
    # Construct the full authorization URL
    auth_url = f"{oauth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    # Redirect the user to Google's authorization page
    return redirect(auth_url)


@login_required
def google_callback(request):
    """
    Callback endpoint for Google OAuth flow.
    """
    # Verify the state parameter to prevent CSRF
    if 'state' not in request.GET or request.GET['state'] != request.session.get('oauth_state'):
        messages.error(request, "Invalid OAuth state. Please try again.")
        return redirect(reverse('users:profile'))
    
    # Clear the state from session
    if 'oauth_state' in request.session:
        del request.session['oauth_state']
    
    # Check for error response
    if 'error' in request.GET:
        error = request.GET['error']
        messages.error(request, f"Google authentication failed: {error}")
        return redirect(reverse('users:profile'))
    
    # Get the authorization code
    if 'code' not in request.GET:
        messages.error(request, "No authorization code received from Google.")
        return redirect(reverse('users:profile'))
    
    code = request.GET['code']
    
    # Exchange the authorization code for an access token
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = request.build_absolute_uri(reverse('users:google_callback'))
    
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        
        # Get the access token
        access_token = token_json.get('access_token')
        if not access_token:
            messages.error(request, "Failed to obtain access token from Google.")
            return redirect(reverse('users:profile'))
        
        # Use the access token to get user info
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        # Update the user's profile with Google information
        user = request.user
        user.google_connected = True
        user.google_id = user_info.get('id')
        user.google_email = user_info.get('email')
        user.google_name = user_info.get('name')
        user.google_picture = user_info.get('picture')
        
        # Store refresh token if provided (for future API calls)
        if 'refresh_token' in token_json:
            user.google_refresh_token = token_json['refresh_token']
            
        user.save()
        
        messages.success(request, "Your Google account has been successfully connected.")
        
        # Redirect to the page the user was on
        return_url = request.session.get('oauth_return_url', reverse('users:profile'))
        if 'oauth_return_url' in request.session:
            del request.session['oauth_return_url']
        
        return redirect(return_url)
    
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Error communicating with Google: {str(e)}")
        return redirect(reverse('users:profile'))


@login_required
def disconnect_google(request):
    """
    Disconnects the user's Google account.
    """
    if request.method != "POST":
        raise SuspiciousOperation("This endpoint requires a POST request")
        
    user = request.user
    
    # Check if the user's account is connected to Google
    if not user.google_connected:
        messages.error(request, "Your account is not connected to Google.")
        return redirect(reverse('users:profile'))
    
    # Revoke the refresh token if we have one
    if hasattr(user, 'google_refresh_token') and user.google_refresh_token:
        revoke_url = "https://oauth2.googleapis.com/revoke"
        
        try:
            requests.post(revoke_url, params={"token": user.google_refresh_token})
        except requests.exceptions.RequestException:
            # Continue even if revoke fails - we'll still disconnect locally
            pass
    
    # Clear Google-related fields
    user.google_connected = False
    user.google_id = ""
    user.google_email = ""
    user.google_name = ""
    user.google_picture = ""
    user.google_refresh_token = ""
    user.save()
    
    messages.success(request, "Your Google account has been disconnected.")
    return redirect(reverse('users:profile'))

@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """
    Handle permanent account deletion
    """
    user = request.user
    
    # Verify confirmation text
    delete_confirmation = request.POST.get('delete_confirmation')
    if delete_confirmation != "DELETE":
        messages.error(request, "Please type DELETE to confirm account deletion.")
        return redirect(reverse('users:profile'))
    
    # Verify password
    password = request.POST.get('password')
    if not password:
        messages.error(request, "Password is required to delete your account.")
        return redirect(reverse('users:profile'))
    
    # Check if password is correct
    if not user.check_password(password):
        messages.error(request, "Incorrect password. Account deletion canceled.")
        return redirect(reverse('users:profile'))
    
    # Check if user understands consequences
    if 'understand_consequences' not in request.POST:
        messages.error(request, "You must acknowledge that you understand the consequences of deleting your account.")
        return redirect(reverse('users:profile'))
    
    # At this point, all validations have passed
    
    try:
        # Begin transaction to delete the user and all related data
        # Store username for logging/message
        username = user.username
        
        # Delete all related data
        # This approach assumes Django's cascading delete will handle related objects
        # If you need more control over deletion order, do it manually here
        
        # For characters
        characters = user.characters.all()
        for character in characters:
            character.delete()
            
        # For conversations
        conversations = user.conversations.all()
        for conversation in conversations:
            conversation.delete()
            
        # For stories
        stories = user.stories.all()
        for story in stories:
            story.delete()
            
        # For worlds
        worlds = user.worlds.all()
        for world in worlds:
            world.delete()
            
        # Finally, delete the user account
        user.delete()
        
        # Log the user out
        logout(request)
        
        # Set a message for the login page
        messages.success(request, f"Your account '{username}' has been permanently deleted. We're sorry to see you go.")
        
        # Redirect to login page
        return redirect(reverse('users:login'))
        
    except Exception as e:
        # If something goes wrong, cancel the deletion
        messages.error(request, f"An error occurred while deleting your account: {str(e)}")
        return redirect(reverse('users:profile'))