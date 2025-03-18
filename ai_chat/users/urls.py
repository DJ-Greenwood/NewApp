# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),  

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/notifications/', views.update_notifications, name='update_notifications'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('profile/disable-2fa/', views.disable_2fa, name='disable_2fa'),
   
    # Google connection URLs
    path('connect/google/', views.connect_google, name='connect_google'),
    path('connect/google/callback/', views.google_callback, name='google_callback'),
    path('disconnect/google/', views.disconnect_google, name='disconnect_google'),

    # Account deletion
    path('delete-account/', views.delete_account, name='delete_account'),

    # Subscription management
    path('subscription/', views.subscription_view, name='subscription'),
  
]