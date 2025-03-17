# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser
from token_management.models import UserTokenLimit

class TokenLimitInline(admin.StackedInline):
    model = UserTokenLimit
    can_delete = False
    verbose_name_plural = 'Token Limits'
    # Update these fields to match your current model
    readonly_fields = ['current_usage', 'last_reset', 'days_until_next_month']
    
    # Define a method to calculate days until next month if needed
    def days_until_next_month(self, obj):
        if obj:
            return obj.days_until_next_month()
        return 0
    days_until_next_month.short_description = "Days Until Reset"

class CustomUserAdmin(UserAdmin):
    # Update the fieldsets to include profile fields but not token fields
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'bio', 'location', 'website')}),
        ('Subscription', {'fields': ('subscription_tier', 'subscription_start_date', 'subscription_end_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Update the add_fieldsets to include only the necessary fields
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'subscription_tier'),
        }),
    )
    
    # Update the list_display to show token info without directly accessing the fields
    list_display = ('username', 'email', 'subscription_tier', 'display_token_usage', 'is_staff')
    
    # Update the readonly_fields to not include token fields
    readonly_fields = ('last_login', 'date_joined')
    
    # Add the TokenLimitInline to display token info
    inlines = [TokenLimitInline]
    
    # Add search and filter fields
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'subscription_tier')
    
    # Custom method to display token usage
    def display_token_usage(self, obj):
        try:
            token_limit = UserTokenLimit.objects.get(user=obj)
            percent = token_limit.get_token_percent_used()
            color = 'green'
            if percent > 80:
                color = 'orange'
            if percent > 95:
                color = 'red'
            
            # Format the percentage separately before passing to format_html
            formatted_percent = "{:.1f}".format(percent)
                
            return format_html(
                '<span style="color: {};">{} / {} ({}%)</span>',
                color,
                token_limit.current_usage,
                token_limit.monthly_limit,
                formatted_percent
            )
        except UserTokenLimit.DoesNotExist:
            return format_html('<span style="color: gray;">No data</span>')
    
    display_token_usage.short_description = 'Token Usage'

admin.site.register(CustomUser, CustomUserAdmin)