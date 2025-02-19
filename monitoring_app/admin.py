from django.contrib import admin
from .models import UserProfile, WeightLog, FoodItem, FoodConsumption, PredictionModel, Message, MealPlan

admin.site.register(UserProfile)
admin.site.register(WeightLog)
admin.site.register(FoodItem)
admin.site.register(FoodConsumption)
admin.site.register(PredictionModel)
admin.site.register(Message)
admin.site.register(MealPlan)