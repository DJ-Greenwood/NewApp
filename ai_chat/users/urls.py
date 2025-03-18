# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),  
    path('profile/', views.profile_view, name='profile'),
    path('profile/notifications/', views.update_notifications, name='update_notifications'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('profile/disable-2fa/', views.disable_2fa, name='disable_2fa'),
   
    # Google connection URLs
    path('connect/google/', views.connect_google, name='connect_google'),
    path('connect/google/callback/', views.google_callback, name='google_callback'),
    path('disconnect/google/', views.disconnect_google, name='disconnect_google'),

        # Account deletion
    path('delete-account/', views.delete_account, name='delete_account'),

    path('preferences/', views.edit_preferences, name='edit_preferences'),
    path('usage/', views.usage_stats, name='usage_stats'),
    path('subscription/', views.subscription_view, name='subscription'),
      # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Password change
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='users/password_change.html'
         ), 
         name='password_change'),
    
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ), 
         name='password_change_done'),
]