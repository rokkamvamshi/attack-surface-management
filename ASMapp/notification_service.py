import requests
import json
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile

def send_severity_notification(user, vulnerability_data):
    """
    Send notifications for high/critical vulnerabilities based on user preferences
    
    Args:
        user: User object for the notification recipient
        vulnerability_data: Dictionary containing vulnerability details
    """
    # Skip if not high or critical severity
    severity = vulnerability_data.get('severity', '').lower()
    if severity not in ['critical', 'high']:
        return
    
    try:
        # Get user profile and check preferences
        profile = UserProfile.objects.get(user=user)
        
        # Skip if user doesn't want critical alerts
        if not profile.critical_alerts:
            return
        
        # Prepare notification message
        domain = vulnerability_data.get('target', '')
        subdomain = vulnerability_data.get('subdomain', '')
        vuln_type = vulnerability_data.get('vulnerability', 'security issue')
        
        subject = f"[{severity.upper()}] Security Alert: {vuln_type} detected"
        message = f"""
        Security Alert: {severity.upper()} severity issue detected!
        
        Target: {domain}
        Subdomain: {subdomain}
        Vulnerability: {vuln_type}
        
        Please check your dashboard for more details and remediation steps.
        """
        
        # Send email notification if preferred
        if profile.notify_via_email:
            send_email_notification(user.email, subject, message)
        
        # Send Slack notification if preferred and webhook URL is set
        if profile.notify_via_slack and profile.slack_webhook_url:
            send_slack_notification(profile.slack_webhook_url, subject, message, severity)
            
    except UserProfile.DoesNotExist:
        # Skip notification if profile doesn't exist
        pass
    except Exception as e:
        # Log the error but don't interrupt the application flow
        print(f"Error sending notification: {str(e)}")

def send_email_notification(recipient_email, subject, message):
    """Send an email notification"""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")

def send_slack_notification(webhook_url, subject, message, severity):
    """Send a Slack notification"""
    try:
        # Define color based on severity
        color = "#ff0000" if severity == "critical" else "#FFA500"  # Red for critical, orange for high
        
        # Format message for Slack
        payload = {
            "attachments": [
                {
                    "fallback": subject,
                    "color": color,
                    "title": subject,
                    "text": message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": severity.upper(),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        # Send the notification
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        # Check for successful response
        if response.status_code != 200:
            print(f"Slack API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Failed to send Slack notification: {str(e)}")