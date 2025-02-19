from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .models import WeightLog, FoodConsumption, FoodItem, UserProfile, PredictionModel, Message, MealPlan, MealItem, Trainer
from .forms import FoodConsumptionForm, MealItemForm, RegisterForm, UserProfileForm, WeightLogForm, FoodConsumptionFormSet, MessageForm, TrainerForm, MealPlanForm, MealItemFormSet
from .analysis.custom_algorithms import CustomFitnessAlgorithms
from django.db.models import Sum, Avg
import json
from datetime import datetime
from django.http import JsonResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from two_factor.views import LoginView as TwoFactorLoginView

class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user'] = self.request.user
        return context

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('edit_profile')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    try:
        profile = UserProfile.objects.get(user=user)
    except ObjectDoesNotExist:
        profile = UserProfile.objects.create(user=user)

    try:
        logs = WeightLog.objects.filter(user=user).order_by('-date')
    except Exception as e:
        logs = WeightLog.objects.none()

    dates = [log.date.strftime('%Y-%m-%d') for log in logs] if logs.exists() else []
    weights = [log.weight for log in logs] if logs.exists() else []
    calories = [log.calories_consumed for log in logs] if logs.exists() else []

    food_data = FoodConsumption.objects.filter(log__in=logs).values('food_item__name').annotate(total_quantity=Sum('quantity')) if logs.exists() else []
    food_labels = [item['food_item__name'] for item in food_data] if food_data else []
    food_values = [item['total_quantity'] for item in food_data] if food_data else []

    # Use custom algorithms for predictions
    predictions, confidence = CustomFitnessAlgorithms.predict_future_weights(user.id) if weights else ([], 0.0)
    all_users = User.objects.all()
    user_ids = [u.id for u in all_users]
    clusters = CustomFitnessAlgorithms.segment_users_by_weight(user_ids) if user_ids else {}
    user_cluster = clusters.get(user.id, 0) if clusters else 0
    arima_forecast = CustomFitnessAlgorithms.forecast_weights_exponential(user.id) if weights else []

    if predictions and isinstance(predictions, list) and len(predictions) > 0:
        for pred_date, pred_weight in predictions:
            PredictionModel.objects.update_or_create(
                user=user,
                prediction_date=datetime.strptime(pred_date, '%Y-%m-%d').date(),
                defaults={'predicted_weight': pred_weight, 'confidence': confidence}
            )

    current_weight = weights[0] if weights else 0
    target_weight = profile.target_weight if profile.target_weight else 0

    progress_percentage = 0
    if target_weight != 0 and current_weight is not None:
        progress_percentage = (current_weight / target_weight) * 100
    else:
        progress_percentage = 0

    recommendations = []
    if logs.exists():
        avg_calories = sum(calories) / len(calories) if calories else 0
        if avg_calories < 1500:
            recommendations.append("Increase calorie intake for better energy.")
        elif avg_calories > 2500:
            recommendations.append("Reduce calorie intake to meet weight goals.")
        recommendations.append("Maintain regular exercise for optimal results.")

    context = {
        'logs': logs,
        'current_weight': current_weight,
        'target_weight': target_weight,
        'progress_percentage': progress_percentage,
        'recommendations': recommendations,
        'dates': dates,
        'weights': weights,
        'calories': calories,
        'food_consumption_data': {'labels': food_labels, 'values': food_values},
        'predictions': predictions,
        'arima_forecast': arima_forecast,
        'clusters': user_cluster,
    }

    return render(request, 'dashboard.html', context)

@login_required
def add_log(request):
    WeightLogFormSet = inlineformset_factory(WeightLog, FoodConsumption, form=FoodConsumptionForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = WeightLogForm(request.POST)
        formset = WeightLogFormSet(request.POST, instance=WeightLog(user=request.user))
        if form.is_valid() and formset.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            formset.instance = log
            formset.save()
            return redirect('dashboard')
    else:
        form = WeightLogForm()
        formset = WeightLogFormSet(instance=WeightLog(user=request.user))
    return render(request, 'add_log.html', {'form': form, 'formset': formset})

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def results(request):
    user = request.user
    predictions = PredictionModel.objects.filter(user=user).order_by('-prediction_date')[:7]
    context = {
        'weight_trend_image': '/static/images/weight_trend.png',
        'user_clusters_image': '/static/images/user_clusters.png',
        'calorie_breakdown_image': '/static/images/calorie_breakdown.png',
        'activity_trend_image': '/static/images/activity_trend.png',
        'predictions': predictions,
    }
    return render(request, 'results.html', context)

@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    return render(request, 'inbox.html', {'messages': messages})

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    return render(request, 'message_detail.html', {'message': message})

@login_required
def create_meal_plan(request):
    MealItemFormSet = inlineformset_factory(MealPlan, MealItem, form=MealItemForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = MealPlanForm(request.POST)
        formset = MealItemFormSet(request.POST, instance=MealPlan(user=request.user))
        if form.is_valid() and formset.is_valid():
            meal_plan = form.save(commit=False)
            meal_plan.user = request.user
            meal_plan.save()
            formset.instance = meal_plan
            formset.save()
            return redirect('dashboard')
    else:
        form = MealPlanForm()
        formset = MealItemFormSet(instance=MealPlan(user=request.user))
    return render(request, 'create_meal_plan.html', {'form': form, 'formset': formset})

@login_required
def send_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')

        try:
            receiver = User.objects.get(id=receiver_id)
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content
            )
            return JsonResponse({'success': True, 'message': 'Message sent successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    users = User.objects.exclude(id=request.user.id)
    return render(request, 'send_message.html', {'users': users})

@login_required
def trainer_dashboard(request):
    trainer, created = Trainer.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = TrainerForm(request.POST, instance=trainer)
        if form.is_valid():
            form.save()
            return redirect('trainer_dashboard')
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'trainer_dashboard.html', {'form': form, 'trainer': trainer})

@login_required
def export_csv(request):
    try:
        logs = WeightLog.objects.filter(user=request.user)
        data = [
            {
                'Date': log.date,
                'Weight': log.weight,
                'Calories': log.calories_consumed,
                'Workout': log.workout_intensity,
                'Steps': log.steps,
                'Sleep': log.sleep_hours,
            } for log in logs
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def export_pdf(request):
    return JsonResponse({'message': 'PDF export not implemented yet'}, status=501)

def logout_view(request):
    logout(request)
    return redirect('index')