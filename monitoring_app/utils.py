from django.db.models import Avg

def generate_dietary_recommendations(user_profile, user_logs):
    if not user_logs.exists():
        return ["Please add some activity logs to receive personalized dietary recommendations."]

    avg_calories = user_logs.aggregate(Avg('calories_consumed'))['calories_consumed__avg'] or 2000

    target_calories = calculate_target_calories(user_profile, avg_calories)

    recommendations = [
        f"Your average daily calorie intake is {avg_calories:.0f} kcal.",
        f"Based on your goals, you should aim for {target_calories:.0f} kcal per day.",
        "Include protein-rich foods like lean meats, beans, and nuts to support muscle growth.",
        "Incorporate more fruits and vegetables for essential vitamins and minerals.",
        "Stay hydrated and limit sugary drinks.",
    ]

    bmi = calculate_bmi(user_profile)
    if bmi:
        if bmi < 18.5:
            recommendations.append("Your BMI indicates you're underweight. Consider consulting a nutritionist.")
        elif bmi > 25:
            recommendations.append("Your BMI indicates you're overweight. Incorporate regular cardio exercises.")
        else:
            recommendations.append("Your BMI is in a healthy range. Keep up the good work!")

    return recommendations

def calculate_target_calories(user_profile, avg_calories):
    if user_profile.target_weight and user_profile.height:
        weight = user_profile.target_weight
        height_cm = user_profile.height * 100
        age = 30
        bmr = 10 * weight + 6.25 * height_cm - 5 * age + 5

        activity_factor = 1.55
        tdee = bmr * activity_factor
        return tdee
    return avg_calories

def calculate_bmi(user_profile):
    if user_profile.height:
        latest_log = user_profile.user.userlog_set.order_by('-date').first()
        if latest_log:
            weight = latest_log.weight
            height = user_profile.height
            bmi = weight / (height ** 2)
            return round(bmi, 2)
    return None