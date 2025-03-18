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

def signup(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create token limit settings
            UserTokenLimit.objects.create(
                user=user,
                monthly_limit=50000  # Default free tier
            )
            
            # Log the user in
            login(request, user)
            messages.success(request, "Registration successful. Welcome to MyImaginaryFriends.ai!")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})

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
    
    return render(request, 'users/login.html')

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
def edit_profile(request):
    """Edit user profile"""
    user = request.user
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserChangeForm(instance=user)
    
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def edit_preferences(request):
    """Edit user preferences"""
    user = request.user
    
    if request.method == 'POST':
        form = UserPreferencesForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Preferences updated successfully.")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserPreferencesForm(user)
    
    return render(request, 'users/edit_preferences.html', {'form': form})

@login_required
def usage_stats(request):
    """View token usage statistics"""
    user = request.user
    
    # Get monthly breakdown
    monthly_stats = []
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    current_year = timezone.now().year
    
    for i, month_name in enumerate(months, 1):
        tokens = TokenUsage.objects.filter(
            user=user,
            timestamp__month=i,
            timestamp__year=current_year
        ).aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
        
        monthly_stats.append({
            'month': month_name,
            'tokens': tokens
        })
    
    # Get feature breakdown
    feature_stats = []
    for feature_code, feature_name in TokenUsage.FEATURE_CHOICES:
        tokens = TokenUsage.objects.filter(
            user=user,
            feature=feature_code
        ).aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
        
        feature_stats.append({
            'feature': feature_name,
            'tokens': tokens
        })
    
    context = {
        'monthly_stats': monthly_stats,
        'feature_stats': feature_stats,
        'total_tokens': sum(item['tokens'] for item in monthly_stats),
    }
    
    return render(request, 'users/usage_stats.html', context)

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
    
    return render(request, 'users/subscription.html', context)

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
    
    return render(request, 'users/signup.html', {
        'form': form,
        'initial_plan': initial_plan
    })


class CustomPasswordResetView(PasswordResetView):
    """
    Custom view for password reset request.
    Displays a form for users to request a password reset email.
    """
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Custom view for password reset request confirmation.
    Shown after a user successfully submits a password reset request.
    """
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom view for password reset confirmation.
    Allows users to set a new password using the link from the reset email.
    """
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Custom view for password reset completion.
    Shown after a user successfully sets a new password.
    """
    template_name = 'users/password_reset_complete.html'

@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    """
    Custom view for changing password.
    Allows authenticated users to change their password.
    """
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    """
    Custom view for password change completion.
    Shown after a user successfully changes their password.
    """
    template_name = 'users/password_change_done.html'

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