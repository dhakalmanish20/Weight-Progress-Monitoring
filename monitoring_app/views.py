from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_protect  # Correct import
from .models import WeightLog, FoodConsumption, FoodItem, UserProfile, PredictionModel, Message
from .analysis.custom_algorithms import CustomAccurateFitnessAlgorithms
from .forms import AccountInfoForm, GoalsForm, SecurityCheckForm, UserCreationWizard
from django.db.models import Sum, Avg
import json
from datetime import datetime
from django.http import JsonResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout

class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user'] = self.request.user
        return context

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

    # Use accurate custom algorithms
    predictions, accuracy = CustomAccurateFitnessAlgorithms.predict_future_weights(user.id) if weights else ([], 0.0)
    all_users = User.objects.all()
    user_ids = [u.id for u in all_users]
    clusters = CustomAccurateFitnessAlgorithms.segment_users_adaptive_clustering(user_ids) if user_ids else {}
    user_cluster = clusters.get(user.id, -1) if user.id in clusters else -1
    ensemble_forecast = CustomAccurateFitnessAlgorithms.forecast_weights_ensemble(user.id) if weights else []

    if predictions and isinstance(predictions, list) and len(predictions) > 0:
        for pred_date, pred_weight, lower_bound, upper_bound in predictions:
            PredictionModel.objects.update_or_create(
                user=user,
                prediction_date=datetime.strptime(pred_date, '%Y-%m-%d').date(),
                defaults={'predicted_weight': pred_weight, 'confidence': accuracy}
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
        'ensemble_forecast': ensemble_forecast,
        'clusters': user_cluster,
        'prediction_accuracy': accuracy,
    }

    return render(request, 'dashboard.html', context)

@login_required
def add_log(request):
    if request.method == 'POST':
        form_data = {
            'weight': request.POST.get('weight', 0),
            'calories_consumed': request.POST.get('calories', 0),
            'workout_intensity': request.POST.get('workout_intensity', 'low'),
            'steps': request.POST.get('steps', 0),
            'sleep_hours': request.POST.get('sleep_hours', 0),
            'heart_rate': request.POST.get('heart_rate', None),
            'blood_pressure': request.POST.get('blood_pressure', None),
            'mood': request.POST.get('mood', 'neutral'),
        }

        try:
            log = WeightLog.objects.create(
                user=request.user,
                weight=float(form_data['weight']),
                calories_consumed=int(form_data['calories_consumed']),
                workout_intensity=form_data['workout_intensity'],
                steps=int(form_data['steps']),
                sleep_hours=float(form_data['sleep_hours']),
                heart_rate=form_data['heart_rate'],
                blood_pressure=form_data['blood_pressure'],
                mood=form_data['mood']
            )
        except (ValueError, TypeError) as e:
            return JsonResponse({'error': f"Invalid input data: {str(e)}"}, status=400)

        food_items = request.POST.getlist('food_items')
        quantities = request.POST.getlist('quantities')
        for food_id, quantity in zip(food_items, quantities):
            if food_id and quantity:
                try:
                    food_item = FoodItem.objects.get(id=food_id)
                    FoodConsumption.objects.create(log=log, food_item=food_item, quantity=float(quantity))
                except (ValueError, TypeError, FoodItem.DoesNotExist) as e:
                    return JsonResponse({'error': f"Failed to add food item: {str(e)}"}, status=400)

        return redirect('dashboard')

    food_items = FoodItem.objects.all()
    return render(request, 'add_log.html', {'food_items': food_items})

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.height = request.POST.get('height')
        profile.target_weight = request.POST.get('target_weight')
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        return redirect('dashboard')

    return render(request, 'edit_profile.html', {'profile': profile})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        step = request.POST.get('step', 'account')
        wizard_data = request.session.get('wizard_data', {})

        forms = {
            'account': AccountInfoForm,
            'goals': GoalsForm,
            'security': SecurityCheckForm
        }

        current_form_class = forms[step]
        current_form = current_form_class(request.POST)

        if current_form.is_valid():
            wizard_data[step] = current_form.cleaned_data
            request.session['wizard_data'] = wizard_data

            if step == 'account':
                return render(request, 'register.html', {
                    'form': GoalsForm(),
                    'step': 'goals',
                    'step1_fields': ['username', 'email', 'password1', 'password2'],
                    'step2_fields': ['height', 'target_weight']
                })
            elif step == 'goals':
                return render(request, 'register.html', {
                    'form': SecurityCheckForm(),
                    'step': 'security',
                    'step1_fields': ['username', 'email', 'password1', 'password2'],
                    'step2_fields': ['height', 'target_weight']
                })
            elif step == 'security':
                wizard = UserCreationWizard(wizard_data)
                try:
                    user = wizard.save()
                    login(request, user)
                    del request.session['wizard_data']
                    return redirect('edit_profile')
                except Exception as e:
                    return render(request, 'register.html', {
                        'form': SecurityCheckForm(),
                        'step': 'security',
                        'step1_fields': ['username', 'email', 'password1', 'password2'],
                        'step2_fields': ['height', 'target_weight'],
                        'error': str(e)
                    })
        else:
            return render(request, 'register.html', {
                'form': current_form,
                'step': step,
                'step1_fields': ['username', 'email', 'password1', 'password2'],
                'step2_fields': ['height', 'target_weight'],
                'errors': current_form.errors
            })

    else:
        # Initial load, show first step
        return render(request, 'register.html', {
            'form': AccountInfoForm(),
            'step': 'account',
            'step1_fields': ['username', 'email', 'password1', 'password2'],
            'step2_fields': ['height', 'target_weight']
        })

def logout_view(request):
    if request.method == 'GET':
        return render(request, 'logout_confirm.html', {'message': 'Are you sure you want to logout?'})
    elif request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)
        return redirect('index')
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def results(request):
    user = request.user
    try:
        predictions = PredictionModel.objects.filter(user=user).order_by('-prediction_date')[:7]
    except Exception as e:
        predictions = []

    context = {
        'predictions': predictions,
    }
    return render(request, 'results.html', context)

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

    users = User.objects.exclude(id=request.user.id)  # Exclude current user
    return render(request, 'send_message.html', {'users': users})

@login_required
def add_log(request):
    if request.method == 'POST':
        form_data = {
            'weight': request.POST.get('weight', 0),
            'calories_consumed': request.POST.get('calories', 0),
            'workout_intensity': request.POST.get('workout_intensity', 'low'),
            'steps': request.POST.get('steps', 0),
            'sleep_hours': request.POST.get('sleep_hours', 0),
            'heart_rate': request.POST.get('heart_rate', None),
            'blood_pressure': request.POST.get('blood_pressure', None),
            'mood': request.POST.get('mood', 'neutral'),
        }

        try:
            log = WeightLog.objects.create(
                user=request.user,
                weight=float(form_data['weight']),
                calories_consumed=int(form_data['calories_consumed']),
                workout_intensity=form_data['workout_intensity'],
                steps=int(form_data['steps']),
                sleep_hours=float(form_data['sleep_hours']),
                heart_rate=form_data['heart_rate'],
                blood_pressure=form_data['blood_pressure'],
                mood=form_data['mood']
            )
        except (ValueError, TypeError) as e:
            return JsonResponse({'error': f"Invalid input data: {str(e)}"}, status=400)

        food_items = request.POST.getlist('food_items')
        quantities = request.POST.getlist('quantities')
        for food_id, quantity in zip(food_items, quantities):
            if food_id and quantity:
                try:
                    food_item = FoodItem.objects.get(id=food_id)
                    FoodConsumption.objects.create(log=log, food_item=food_item, quantity=float(quantity))
                except (ValueError, TypeError, FoodItem.DoesNotExist) as e:
                    return JsonResponse({'error': f"Failed to add food item: {str(e)}"}, status=400)

        return redirect('dashboard')

    food_items = FoodItem.objects.all()
    return render(request, 'add_log.html', {'food_items': food_items})

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.height = request.POST.get('height')
        profile.target_weight = request.POST.get('target_weight')
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        return redirect('dashboard')

    return render(request, 'edit_profile.html', {'profile': profile})