from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    """Enhanced user creation form with email field"""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        
        # Check if email already exists for a different user
        if User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('This email is already in use by another account.')
        
        return email

class ApiKeyForm(forms.Form):
    """Form for generating API keys"""
    name = forms.CharField(max_length=100, required=True, 
                          label="API Key Name",
                          help_text="Enter a name to identify this API key")
    
    expires = forms.ChoiceField(choices=[
        ('30', '30 Days'),
        ('90', '90 Days'),
        ('180', '180 Days'),
        ('365', '365 Days'),
        ('0', 'Never Expires')
    ], required=True, label="Expiration")