from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from datetime import datetime, timedelta
from django.db import models
import stripe
from django.utils import timezone
from django.db.models import Sum
from django.http import JsonResponse

from .models import TokenPurchase, TokenUsage, UserTokenLimit, TokenHistory

# Set up Stripe API
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def overview(request):
    """Main overview page showing token status, usage, and purchase options."""
    user = request.user
    
    # Get user's current token balance
    try:
        token_limit = UserTokenLimit.objects.get(user=user)
    except UserTokenLimit.DoesNotExist:
        token_limit = UserTokenLimit.objects.create(user=user, monthly_limit=100)
    
    # Calculate token usage for current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    token_usage_this_month = TokenUsage.objects.filter(
        user=user,
        timestamp__month=current_month,
        timestamp__year=current_year
    ).values('amount').aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Calculate percentage of usage
    token_percent = (token_usage_this_month / token_limit.monthly_limit) * 100 if token_limit.monthly_limit > 0 else 0
    
    # Get recent usage history
    recent_usage = TokenUsage.objects.filter(user=user).order_by('-timestamp')[:5]
    
    # Get recent purchases
    recent_purchases = TokenPurchase.objects.filter(user=user).order_by('-purchase_date')[:3]
    
    context = {
        'token_limit': token_limit.monthly_limit,
        'token_usage': token_usage_this_month,
        'token_percent': token_percent,
        'recent_usage': recent_usage,
        'recent_purchases': recent_purchases,
        'has_subscription': user.profile.subscription_level != 'free'
    }
    
    return render(request, 'token_management/overview.html', context)

@login_required
def purchase_tokens(request):
    """Page for purchasing additional tokens."""
    if request.method == 'POST':
        # Handle form submission for token purchase
        token_package = request.POST.get('token_package')
        
        # Create Stripe checkout session
        try:
            price_id = get_price_id_for_package(token_package)
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/tokens/checkout/success/'),
                cancel_url=request.build_absolute_uri('/tokens/checkout/cancel/'),
                client_reference_id=request.user.id,
                metadata={
                    'token_package': token_package
                }
            )
            
            return redirect(checkout_session.url)
            
        except Exception as e:
            messages.error(request, f"Error creating checkout session: {str(e)}")
            return redirect('token_management:purchase_tokens')
    
    # Prepare token packages for display
    token_packages = [
        {'id': 'basic', 'tokens': 1000, 'price': 4.99, 'popular': False},
        {'id': 'standard', 'tokens': 5000, 'price': 19.99, 'popular': True},
        {'id': 'premium', 'tokens': 15000, 'price': 49.99, 'popular': False},
    ]
    
    return render(request, 'token_management/purchase.html', {'token_packages': token_packages})

@login_required
def token_history(request):
    """Page showing the history of token usage and purchases."""
    # Get date range for filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Query token usage
    usage_history = TokenUsage.objects.filter(
        user=request.user,
        timestamp__range=[start_date, end_date]
    ).order_by('-timestamp')
    
    # Query token purchases
    purchase_history = TokenPurchase.objects.filter(
        user=request.user,
        purchase_date__range=[start_date, end_date]
    ).order_by('-purchase_date')
    
    context = {
        'usage_history': usage_history,
        'purchase_history': purchase_history,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'token_management/history.html', context)

@login_required
def subscription_management(request):
    """Page for managing token subscriptions."""
    user = request.user
    
    # Get current subscription status
    subscription_level = user.profile.subscription_level
    
    # Prepare subscription plans for display
    subscription_plans = [
        {
            'id': 'basic',
            'name': 'Basic',
            'tokens_per_month': 5000,
            'price': 9.99,
            'features': ['5,000 tokens monthly', 'Basic character creation', 'Standard support']
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'tokens_per_month': 20000,
            'price': 29.99,
            'features': ['20,000 tokens monthly', 'Advanced character creation', 'Priority support', 'Story generation']
        },
        {
            'id': 'unlimited',
            'name': 'Unlimited',
            'tokens_per_month': 100000,
            'price': 99.99,
            'features': ['100,000 tokens monthly', 'All features unlocked', 'Premium support', 'Early access to new features']
        }
    ]
    
    context = {
        'subscription_level': subscription_level,
        'subscription_plans': subscription_plans
    }
    
    return render(request, 'token_management/subscription.html', context)

@login_required
def checkout_success(request):
    """Handle successful Stripe checkout."""
    session_id = request.GET.get('session_id')
    
    try:
        # Retrieve checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Get token package from metadata
        token_package = session.metadata.get('token_package')
        token_amount = get_token_amount_for_package(token_package)
        
        # Record the purchase
        purchase = TokenPurchase.objects.create(
            user=request.user,
            amount=token_amount,
            cost=session.amount_total / 100,  # Convert from cents to dollars
            payment_id=session.payment_intent
        )
        
        # Update user's token limit
        token_limit, created = UserTokenLimit.objects.get_or_create(user=request.user)
        token_limit.monthly_limit += token_amount
        token_limit.save()
        
        messages.success(request, f"Successfully purchased {token_amount} tokens!")
        
    except Exception as e:
        messages.error(request, f"Error processing purchase: {str(e)}")
    
    return redirect('token_management:overview')

@login_required
def checkout_cancel(request):
    """Handle canceled Stripe checkout."""
    messages.warning(request, "Token purchase was canceled.")
    return redirect('token_management:purchase_tokens')

@login_required
def token_usage_api(request):
    """API endpoint for token usage statistics."""
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get daily usage data
    usage_data = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_usage = TokenUsage.objects.filter(
            user=request.user,
            timestamp__date=current_date.date()
        ).values('amount').aggregate(total=models.Sum('amount'))['total'] or 0
        
        usage_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'tokens': daily_usage
        })
        
        current_date += timedelta(days=1)
    
    return JsonResponse({'usage_data': usage_data})

@login_required
def usage_settings(request):
    """Page for configuring token usage settings and alerts."""
    user = request.user
    token_limit, created = UserTokenLimit.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Update usage settings
        try:
            # Update alert thresholds
            token_limit.alert_threshold = int(request.POST.get('alert_threshold', 80))
            token_limit.save()
            
            messages.success(request, "Usage settings updated successfully.")
            
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")
    
    context = {
        'token_limit': token_limit,
    }
    
    return render(request, 'token_management/settings.html', context)

# Helper functions
def get_price_id_for_package(package_id):
    """Get the Stripe price ID for the given token package."""
    # These would be configured in your settings or database
    price_mapping = {
        'basic': 'price_1234basic',
        'standard': 'price_1234standard',
        'premium': 'price_1234premium',
    }
    return price_mapping.get(package_id)

def get_token_amount_for_package(package_id):
    """Get the token amount for the given package ID."""
    token_mapping = {
        'basic': 1000,
        'standard': 5000,
        'premium': 15000,
    }
    return token_mapping.get(package_id, 0)

@login_required
def usage_history(request):
    """View to display historical token usage"""
    # Get current year or from query params
    year = request.GET.get('year', timezone.now().year)
    try:
        year = int(year)
    except ValueError:
        year = timezone.now().year
    
    # Get monthly history for the year
    monthly_history = TokenHistory.objects.filter(
        user=request.user,
        year=year
    ).order_by('month')
    
    # Get yearly summaries for dropdown
    available_years = TokenHistory.objects.filter(
        user=request.user
    ).values_list('year', flat=True).distinct().order_by('-year')
    
    # Get current month's usage
    token_limit = UserTokenLimit.objects.get(user=request.user)
    current_month_data = {
        'month': timezone.now().month,
        'year': timezone.now().year,
        'total_usage': token_limit.current_usage,
        'allocated_limit': token_limit.monthly_limit,
        'percent_used': token_limit.get_token_percent_used(),
    }
    
    # Calculate feature usage breakdown
    feature_breakdown = TokenUsage.objects.filter(
        user=request.user,
        timestamp__year=timezone.now().year,
        timestamp__month=timezone.now().month
    ).values('feature').annotate(
        total=Sum('tokens_used')
    ).order_by('-total')
    
    context = {
        'monthly_history': monthly_history,
        'current_month': current_month_data,
        'selected_year': year,
        'available_years': available_years,
        'feature_breakdown': feature_breakdown,
    }
    
    return render(request, 'token_management/usage_history.html', context)

@login_required
def trial_conversion(request):
    """View for trial to paid conversion"""
    token_limit = UserTokenLimit.objects.get(user=request.user)
    
    if request.method == 'POST':
        selected_plan = request.POST.get('subscription_plan')
        
        # Create checkout session with Stripe or your payment processor
        # ...
        
        # Mark that user has seen conversion dialog
        token_limit.has_seen_conversion = True
        token_limit.save(update_fields=['has_seen_conversion'])
        
        return redirect('payment_checkout_url')
    
    # Calculate trial stats to show user
    trial_stats = {
        'days_used': 14 - token_limit.days_left_in_trial(),
        'tokens_used': token_limit.current_usage,
        'characters_created': 0,  # You'd calculate this from your character model
        'conversations_had': 0,   # You'd calculate this from your conversation model
    }
    
    # Get subscription plans
    subscription_plans = [
        {
            'id': 'basic',
            'name': 'Basic',
            'tokens_per_month': 100000,
            'price': 9.99,
            'features': ['100,000 tokens monthly', '10 characters', 'Standard support']
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'tokens_per_month': 250000,
            'price': 19.99,
            'features': ['250,000 tokens monthly', '25 characters', 'Priority support', 'Advanced features']
        },
        {
            'id': 'unlimited',
            'name': 'Professional',
            'tokens_per_month': 500000,
            'price': 29.99,
            'features': ['500,000 tokens monthly', 'Unlimited characters', 'Premium support', 'All features']
        }
    ]
    
    context = {
        'token_limit': token_limit,
        'trial_stats': trial_stats,
        'subscription_plans': subscription_plans,
        'days_left': token_limit.days_left_in_trial(),
    }
    
    return render(request, 'token_management/trial_conversion.html', context)

@login_required
def mark_conversion_seen(request):
    """Mark that the user has seen the conversion popup"""
    if request.method == 'POST':
        try:
            token_limit = UserTokenLimit.objects.get(user=request.user)
            token_limit.has_seen_conversion = True
            token_limit.save(update_fields=['has_seen_conversion'])
            return JsonResponse({'status': 'success'})
        except UserTokenLimit.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User token limit not found'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)