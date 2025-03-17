from django.urls import path
from . import views

app_name = 'token_management'

urlpatterns = [
    # Overview page showing token status
    path('', views.overview, name='overview'),
    path('overview/', views.overview, name='overview'),
    
    # Token purchase and management
    path('purchase/', views.purchase_tokens, name='purchase_tokens'),
    path('history/', views.token_history, name='token_history'),
    path('history/', views.usage_history, name='usage_history'),
    
    # Subscription management
    path('subscription/', views.subscription_management, name='subscription'),
    
    # Payment processing
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('checkout/cancel/', views.checkout_cancel, name='checkout_cancel'),
    
    # API endpoints for token usage
    path('api/usage/', views.token_usage_api, name='token_usage_api'),
    
    # Usage settings and limits
    path('settings/', views.usage_settings, name='usage_settings'),
    
    # Trial conversion
    path('trial/conversion/', views.trial_conversion, name='trial_conversion'),
    path('trial/mark-seen/', views.mark_conversion_seen, name='mark_conversion_seen'),
]