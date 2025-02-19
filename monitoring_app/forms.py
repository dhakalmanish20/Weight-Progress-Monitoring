from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from captcha.fields import CaptchaField

class AccountInfoForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class GoalsForm(forms.Form):
    height = forms.FloatField(required=False, label='Height (m)')
    target_weight = forms.FloatField(required=False, label='Target Weight (kg)')

class SecurityCheckForm(forms.Form):
    captcha = CaptchaField()

class UserCreationWizard:
    def __init__(self, data=None):
        self.data = data or {}
        self.steps = ['account', 'goals', 'security']

    def get_form_data(self, step):
        return self.data.get(step, {})

    def is_valid(self):
        required_steps = ['account', 'goals', 'security']
        return all(self.data.get(step) for step in required_steps)

    def save(self):
        if not self.is_valid():
            raise ValueError("All steps must be completed and valid")

        account_data = self.data['account']
        goals_data = self.data['goals']

        # Create user
        user = User.objects.create_user(
            username=account_data['username'],
            email=account_data['email'],
            password=account_data['password1']
        )

        # Create or update UserProfile
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.height = goals_data.get('height')
        user_profile.target_weight = goals_data.get('target_weight')
        user_profile.save()

        return user