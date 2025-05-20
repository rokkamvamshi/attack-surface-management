from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ScanResult(models.Model):
    """Model for storing subdomain scan results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target = models.CharField(max_length=255)
    subdomains = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan for {self.target} by {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Domain Scan Result'
        verbose_name_plural = 'Domain Scan Results'


class NucleiResult(models.Model):
    """Model for storing vulnerability scan results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=255)
    bug_class = models.CharField(max_length=255)
    scan_results = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vulnerability scan for {self.subdomain} ({self.bug_class})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vulnerability Scan Result'
        verbose_name_plural = 'Vulnerability Scan Results'


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_onboarding = models.BooleanField(default=False)
    
    # Existing preferences
    email_notifications = models.BooleanField(default=True)
    critical_alerts = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=False)
    
    # Add new notification channel preferences
    notify_via_email = models.BooleanField(default=True)
    notify_via_slack = models.BooleanField(default=False)
    slack_webhook_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class UserActivity(models.Model):
    """User activity tracking"""
    ACTIVITY_TYPES = (
        ('scan', 'Scan'),
        ('login', 'Login'),
        ('update', 'Profile Update'),
        ('password', 'Password Change')
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"


class ApiKey(models.Model):
    """API keys for programmatic access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def masked_key(self):
        """Return a masked version of the key for display"""
        if not self.key:
            return ""
        return f"{self.key[:8]}...{self.key[-4:]}"
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'


class UserFeedback(models.Model):
    """User feedback collection"""
    FEEDBACK_TYPES = (
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('usability', 'Usability Issue'),
        ('praise', 'Praise'),
        ('other', 'Other')
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    rating = models.IntegerField(null=True, blank=True)
    feedback_text = models.TextField()
    contact_consent = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True)
    page_url = models.URLField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_display = self.user.username if self.user else 'Anonymous'
        return f"{self.get_feedback_type_display()} from {user_display}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'