from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.FloatField(default=1.75)
    target_weight = models.FloatField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    friends = models.ManyToManyField("self", blank=True, symmetrical=False)

    def __str__(self):
        return self.user.username

    def bmi(self):
        latest_log = self.user.userlog_set.order_by('-date').first()
        if latest_log:
            return round(latest_log.weight / (self.height ** 2), 2)
        return None

class FoodItem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    serving_size = models.FloatField()
    calories = models.FloatField()
    protein = models.FloatField()
    fat = models.FloatField()
    carbs = models.FloatField()

    def __str__(self):
        return self.name

class UserLog(models.Model):
    WORKOUT_INTENSITY_CHOICES = [(1, 'Light'), (2, 'Moderate'), (3, 'Intense')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    weight = models.FloatField()
    calories_consumed = models.FloatField()
    workout_intensity = models.IntegerField(choices=WORKOUT_INTENSITY_CHOICES)
    steps = models.IntegerField(default=0)
    sleep_hours = models.FloatField(default=0.0)
    mood = models.CharField(max_length=50, null=True, blank=True)
    heart_rate = models.IntegerField(default=0)
    blood_pressure = models.CharField(max_length=7, null=True, blank=True)
    food_items = models.ManyToManyField(FoodItem, through='FoodConsumption')

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class FoodConsumption(models.Model):
    user_log = models.ForeignKey(UserLog, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.FloatField()

    def __str__(self):
        return f"{self.food_item.name} on {self.user_log.date}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Msg from {self.sender.username} to {self.receiver.username}"

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    certification = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Trainer {self.user.username}"

class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    total_calories = models.FloatField(default=0.0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"MealPlan({self.name}) for {self.user.username}"

class MealItem(models.Model):
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='meal_items')
    name = models.CharField(max_length=100)
    serving_size = models.FloatField(default=100)
    calories = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    carbs = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name} ({self.meal_plan.name})"