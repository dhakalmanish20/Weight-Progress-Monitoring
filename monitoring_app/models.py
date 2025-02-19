from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    target_weight = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    friends = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField(auto_now_add=True)
    weight = models.FloatField(validators=[MinValueValidator(0)])
    calories_consumed = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    workout_intensity = models.CharField(max_length=50, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low')
    steps = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    sleep_hours = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(24)])
    heart_rate = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    blood_pressure = models.CharField(max_length=10, null=True, blank=True)
    mood = models.CharField(max_length=50, choices=[('happy', 'Happy'), ('neutral', 'Neutral'), ('sad', 'Sad')], default='neutral')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.weight} kg"

class FoodItem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, help_text="e.g., Vegetables, Proteins, Carbs")
    calories = models.IntegerField(validators=[MinValueValidator(0)], help_text="Calories per 100g")
    protein = models.FloatField(validators=[MinValueValidator(0)], help_text="Protein in grams per 100g")
    fat = models.FloatField(validators=[MinValueValidator(0)], help_text="Fat in grams per 100g")
    carbs = models.FloatField(validators=[MinValueValidator(0)], help_text="Carbohydrates in grams per 100g")
    serving_size = models.FloatField(default=100, validators=[MinValueValidator(0)], help_text="Default serving size in grams")

    def __str__(self):
        return self.name

    def get_nutrients_for_quantity(self, quantity):
        ratio = quantity / self.serving_size
        return {
            'calories': self.calories * ratio,
            'protein': self.protein * ratio,
            'fat': self.fat * ratio,
            'carbs': self.carbs * ratio
        }

class FoodConsumption(models.Model):
    log = models.ForeignKey(WeightLog, on_delete=models.CASCADE, related_name='foodconsumption_set')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.FloatField(validators=[MinValueValidator(0)], help_text="Quantity consumed in grams")

    def __str__(self):
        return f"{self.food_item.name} - {self.quantity}g for {self.log.user.username}"

    @property
    def nutrients(self):
        return self.food_item.get_nutrients_for_quantity(self.quantity)

class PredictionModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    predicted_weight = models.FloatField(null=True, blank=True)
    prediction_date = models.DateField(auto_now_add=True)
    confidence = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])

    class Meta:
        ordering = ['-prediction_date']

    def __str__(self):
        return f"Prediction for {self.user.username} on {self.prediction_date}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    name = models.CharField(max_length=100)
    total_calories = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Meal Plan: {self.name} for {self.user.username}"

class MealItem(models.Model):
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='meal_items')
    name = models.CharField(max_length=100)
    serving_size = models.FloatField(validators=[MinValueValidator(0)])
    calories = models.IntegerField(validators=[MinValueValidator(0)])
    protein = models.FloatField(validators=[MinValueValidator(0)])
    fat = models.FloatField(validators=[MinValueValidator(0)])
    carbs = models.FloatField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.name} in {self.meal_plan.name}"

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer')
    certification = models.CharField(max_length=200)
    bio = models.TextField()
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Trainer {self.user.username}"