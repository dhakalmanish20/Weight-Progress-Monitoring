import os
import matplotlib.pyplot as plt
from monitoring_app.models import FoodItem

def calorie_estimation(food_dict):
    total_calories = 0
    macronutrients = {'Protein': 0, 'Fat': 0, 'Carbs': 0}

    for food, quantity in food_dict.items():
        try:
            food_item = FoodItem.objects.get(name__iexact=food)
            factor = quantity / food_item.serving_size
            total_calories += factor * food_item.calories
            macronutrients['Protein'] += factor * food_item.protein
            macronutrients['Fat'] += factor * food_item.fat
            macronutrients['Carbs'] += factor * food_item.carbs
        except FoodItem.DoesNotExist:
            continue

    labels = list(macronutrients.keys())
    values = list(macronutrients.values())

    output_path = 'monitoring_app/static/images/calorie_breakdown.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.figure(figsize=(8, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Calorie Breakdown')
    plt.savefig(output_path)
    plt.close()