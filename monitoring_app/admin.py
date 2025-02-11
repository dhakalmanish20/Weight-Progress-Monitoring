from django.contrib import admin
from .models import (
    FoodItem, UserProfile, UserLog, Message,
    Trainer, MealPlan, MealItem
)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'serving_size', 'calories', 'protein', 'fat', 'carbs')
    search_fields = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'height', 'target_weight')
    filter_horizontal = ('friends',)

class FoodConsumptionInline(admin.TabularInline):
    model = UserLog.food_items.through
    extra = 1

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'calories_consumed', 'workout_intensity', 'steps', 'mood')
    list_filter = ('user', 'date', 'workout_intensity')
    search_fields = ('user__username', 'mood')
    inlines = [FoodConsumptionInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'certification', 'hourly_rate')

class MealItemInline(admin.TabularInline):
    model = MealItem
    extra = 1

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'total_calories')
    inlines = [MealItemInline]

@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ('meal_plan', 'name', 'serving_size', 'calories', 'protein', 'fat', 'carbs')
    search_fields = ('meal_plan__name', 'name')