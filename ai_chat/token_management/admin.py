from django.contrib import admin
from .models import UserTokenLimit, TokenUsage, TokenAlert, TokenPurchase, TokenHistory

@admin.register(UserTokenLimit)
class UserTokenLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_limit', 'current_usage', 'alert_threshold', 'is_trial', 'last_reset')
    search_fields = ('user__username',)
    list_filter = ('is_trial', 'last_reset')
    readonly_fields = ('last_reset', 'current_usage')

@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'feature', 'tokens_used', 'timestamp')
    search_fields = ('user__username', 'feature')
    list_filter = ('feature', 'timestamp')
    ordering = ('-timestamp',)

@admin.register(TokenAlert)
class TokenAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'threshold', 'is_acknowledged', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('threshold', 'is_acknowledged', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_as_acknowledged']

    def mark_as_acknowledged(self, request, queryset):
        queryset.update(is_acknowledged=True)
    mark_as_acknowledged.short_description = "Mark selected alerts as acknowledged"

@admin.register(TokenPurchase)
class TokenPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'tokens_purchased', 'amount_paid', 'payment_status', 'created_at')
    search_fields = ('user__username', 'payment_status')
    list_filter = ('payment_status', 'created_at')
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')

@admin.register(TokenHistory)
class TokenHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'year', 'total_usage', 'allocated_limit', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('year', 'month')
    ordering = ('-year', '-month')
