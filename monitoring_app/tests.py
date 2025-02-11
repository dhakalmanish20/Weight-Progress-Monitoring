from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import (
    UserProfile, UserLog, FoodItem, FoodConsumption,
    Message, Trainer, MealPlan, MealItem
)
from datetime import datetime
from django.utils import timezone

class UserProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
        self.profile = UserProfile.objects.create(user=self.user, height=1.80, target_weight=75)

    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testuser')

    def test_bmi_calculation(self):
        UserLog.objects.create(user=self.user, weight=80, calories_consumed=2000, workout_intensity=2)
        self.assertEqual(self.profile.bmi(), round(80 / (1.80 ** 2), 2))

class APITestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user('apiuser', 'api@example.com', 'apipass')
        UserLog.objects.create(user=self.user, weight=70, calories_consumed=1800, workout_intensity=2)

    def test_weight_prediction_api(self):
        self.c.login(username='apiuser', password='apipass')
        resp = self.c.post(reverse('weight_prediction_api'), {
            'calories': 2000, 'workout_intensity': 2, 'steps': 8000, 'sleep_hours': 7, 'heart_rate': 70
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('predicted_weight', resp.json())