from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, UserLog, FoodItem, FoodConsumption, Message,
    Trainer, MealPlan, MealItem
)
from two_factor.forms import AuthenticationTokenForm, DeviceValidationForm
from captcha.fields import CaptchaField

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    height = forms.FloatField(required=True, label='Height (m)')
    target_weight = forms.FloatField(required=False, label='Target Weight (kg)')
    captcha = CaptchaField()
    class Meta:
        model = User
        fields = ["username", "email", "height", "target_weight", "password1", "password2"]
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                height=self.cleaned_data['height'],
                target_weight=self.cleaned_data.get('target_weight')
            )
        return user

class UserProfileForm(forms.ModelForm):
    friends = forms.ModelMultipleChoiceField(
        queryset=UserProfile.objects.exclude(user__username='admin'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class':'form-control'})
    )
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class':'form-control-file'}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows':4}), required=False)
    class Meta:
        model = UserProfile
        fields = ['height', 'target_weight', 'bio', 'friends', 'profile_picture']

class FoodConsumptionForm(forms.ModelForm):
    class Meta:
        model = FoodConsumption
        fields = ['food_item', 'quantity']

FoodConsumptionFormSet = forms.inlineformset_factory(
    UserLog,
    FoodConsumption,
    form=FoodConsumptionForm,
    extra=1,
    can_delete=True
)

class UserLogForm(forms.ModelForm):
    class Meta:
        model = UserLog
        fields = [
            'weight', 'calories_consumed', 'workout_intensity', 'steps',
            'sleep_hours', 'mood', 'heart_rate', 'blood_pressure'
        ]
        widgets = {'workout_intensity': forms.RadioSelect()}

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
        widgets = {
            'receiver': forms.Select(attrs={'class':'form-control'}),
            'content': forms.Textarea(attrs={'class':'form-control','rows':4}),
        }

class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['certification', 'bio', 'hourly_rate']

class MealItemForm(forms.ModelForm):
    class Meta:
        model = MealItem
        fields = ['name', 'serving_size', 'calories', 'protein', 'fat', 'carbs']

MealItemFormSet = forms.inlineformset_factory(
    MealPlan,
    MealItem,
    form=MealItemForm,
    extra=1,
    can_delete=True
)

class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['name', 'total_calories', 'notes']