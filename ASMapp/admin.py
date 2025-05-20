from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import ScanResult, NucleiResult, UserProfile, UserActivity, ApiKey, UserFeedback

# Unregister the default User admin
admin.site.unregister(User)

class CustomUserAdmin(UserAdmin):
    """Custom User admin with enhanced display"""
    model = User
    list_display = ['username', 'email', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['username']
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets


class ScanResultAdmin(admin.ModelAdmin):
    """Admin for ScanResult model"""
    list_display = ('user', 'target', 'created_at')
    search_fields = ('target', 'user__username')
    list_filter = ('created_at', 'user')
    readonly_fields = ('created_at',)


class NucleiResultAdmin(admin.ModelAdmin):
    """Admin for NucleiResult model"""
    list_display = ('user', 'target', 'subdomain', 'bug_class', 'created_at')
    search_fields = ('target', 'subdomain', 'user__username')
    list_filter = ('created_at', 'bug_class', 'user')
    readonly_fields = ('created_at',)


class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    list_display = ('user', 'company', 'completed_onboarding', 'created_at')
    search_fields = ('user__username', 'company')
    list_filter = ('completed_onboarding', 'email_notifications', 'created_at')
    readonly_fields = ('created_at',)


class UserActivityAdmin(admin.ModelAdmin):
    """Admin for UserActivity model"""
    list_display = ('user', 'activity_type', 'description', 'timestamp')
    search_fields = ('user__username', 'description')
    list_filter = ('activity_type', 'timestamp')
    readonly_fields = ('timestamp',)


class ApiKeyAdmin(admin.ModelAdmin):
    """Admin for ApiKey model"""
    list_display = ('user', 'name', 'masked_key', 'created_at', 'last_used', 'expires_at')
    search_fields = ('user__username', 'name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'masked_key')


class UserFeedbackAdmin(admin.ModelAdmin):
    """Admin for UserFeedback model"""
    list_display = ('user', 'feedback_type', 'rating', 'contact_consent', 'created_at')
    search_fields = ('user__username', 'feedback_text', 'email')
    list_filter = ('feedback_type', 'rating', 'created_at')
    readonly_fields = ('created_at',)


# Register all models with their admin classes
admin.site.register(User, CustomUserAdmin)
admin.site.register(ScanResult, ScanResultAdmin)
admin.site.register(NucleiResult, NucleiResultAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(UserFeedback, UserFeedbackAdmin)