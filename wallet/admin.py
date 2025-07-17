from django.contrib import admin
from django.utils.html import format_html
from .models import Wallet, WalletTransaction, UserMargin

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'user_type', 'created_at', 'updated_at')
    list_filter = ('user__user_type', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username', 'user__phone')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_type(self, obj):
        return obj.user.user_type.title()
    user_type.short_description = 'User Type'

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_user', 'transaction_type', 'amount', 'created_by', 'created_at')
    list_filter = ('transaction_type', 'created_at', 'wallet__user__user_type')
    search_fields = ('wallet__user__email', 'wallet__user__username', 'description')
    readonly_fields = ('created_at',)
    
    def wallet_user(self, obj):
        return obj.wallet.user.email
    wallet_user.short_description = 'Wallet User'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wallet__user', 'created_by')

@admin.register(UserMargin)
class UserMarginAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'margin_percentage', 'admin', 'created_at', 'updated_at')
    list_filter = ('user__user_type', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username', 'admin__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_type(self, obj):
        return obj.user.user_type.title()
    user_type.short_description = 'User Type'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'admin')