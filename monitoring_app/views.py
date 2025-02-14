import os  
import json  
import logging  
import warnings  
from datetime import datetime  
from django.conf import settings  
from django.shortcuts import render, redirect, get_object_or_404  
from django.views import View  
from django.contrib.auth import logout  
from django.contrib import messages  
from django.contrib.auth.mixins import LoginRequiredMixin  
from django.contrib.auth.decorators import login_required  
from django.utils.decorators import method_decorator  
from django.views.decorators.csrf import csrf_exempt  
from django.http import JsonResponse, HttpResponse  
from django.urls import reverse  
import pandas as pd  
import numpy as np  
import matplotlib.pyplot as plt  
from statsmodels.tsa.statespace.sarimax import SARIMAX  
from pmdarima import auto_arima  
from sklearn.metrics import mean_absolute_error, mean_squared_error  
from reportlab.pdfgen import canvas  
from reportlab.lib.pagesizes import letter  
from two_factor.views import LoginView as TwoFactorLoginView  
from sklearn.linear_model import LinearRegression  
  
# Suppress warnings  
warnings.filterwarnings('ignore')  
  
# Configure logging  
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  
  
from .models import (  
    UserProfile, UserLog, FoodConsumption, FoodItem,  
    Message, Trainer, MealPlan, MealItem  
)  
from .forms import (  
    RegisterForm, UserProfileForm, UserLogForm, FoodConsumptionFormSet,  
    MessageForm, TrainerForm, MealPlanForm, MealItemFormSet  
)  
  
class IndexView(View):  
    def get(self, request):  
        return render(request, 'index.html')  
  
class CustomLoginView(TwoFactorLoginView):  
    template_name = 'login.html'  
  
@login_required  
def logout_view(request):  
    logout(request)  
    return redirect('index')  
  
class RegisterView(View):  
    def get(self, request):  
        return render(request, 'register.html', {'form': RegisterForm()})  
  
    def post(self, request):  
        form = RegisterForm(request.POST)  
        if form.is_valid():  
            form.save()  
            messages.success(request, 'Registration successful.')  
            return redirect('two_factor:login')  
        return render(request, 'register.html', {'form': form})  
  
class DashboardView(LoginRequiredMixin, View):  
    def get(self, request):  
        up, _ = UserProfile.objects.get_or_create(user=request.user)  
        logs = UserLog.objects.filter(user=request.user).order_by('-date')  
        dates = list(logs.values_list('date', flat=True))  
        ds = [d.strftime('%Y-%m-%d') for d in dates]  
        weights = list(logs.values_list('weight', flat=True))  
        cals = list(logs.values_list('calories_consumed', flat=True))  
        moods = list(logs.values_list('mood', flat=True))  
          
        if weights:  
            cw = weights[0]  
            tw = up.target_weight or cw  
            prog = max(0, min(100, (abs(cw - tw) / (cw if cw != 0 else 1) * 100)))  
        else:  
            cw = 0  
            tw = 0  
            prog = 0  
          
        fm = {}  
        for lg in logs:  
            for fc in FoodConsumption.objects.filter(user_log=lg):  
                fm[fc.food_item.name] = fm.get(fc.food_item.name, 0) + fc.quantity  
          
        fd = {  
            'labels': list(fm.keys()),  
            'values': list(fm.values()),  
        }  
          
        fd_friends = []  
          
        # Fetch calorie forecast  
        pred, forecast_image = calorie_forecast_sarima(request)  
          
        forecast_data = None  
        if pred is not None:  
            forecast_data = {  
                'dates': pred.index.strftime('%Y-%m-%d').tolist(),  
                'values': pred.round(2).tolist(),  
            }  
          
        ctx = {  
            'logs': logs,  
            'dates_json': json.dumps(ds),  
            'weights_json': json.dumps(weights),  
            'calories_json': json.dumps(cals),  
            'moods_json': json.dumps(moods),  
            'food_consumption_data_json': json.dumps(fd),  
            'progress_percentage_json': json.dumps(prog),  
            'friends_data_json': json.dumps(fd_friends),  
            'current_weight': cw,  
            'target_weight': tw,  
            'friends': up.friends.all(),  
            'user_profile': up,  
            'forecast_data': forecast_data,  
            'forecast_image': forecast_image,  
        }  
        return render(request, 'dashboard.html', ctx)  
  
class AddLogView(LoginRequiredMixin, View):  
    def get(self, request):  
        return render(request, 'add_log.html', {  
            'user_log_form': UserLogForm(),  
            'food_formset': FoodConsumptionFormSet(queryset=FoodConsumption.objects.none())  
        })  
  
    def post(self, request):  
        frm = UserLogForm(request.POST)  
        frm2 = FoodConsumptionFormSet(request.POST)  
        if frm.is_valid() and frm2.is_valid():  
            obj = frm.save(commit=False)  
            obj.user = request.user  
            obj.save()  
            frm2.instance = obj  
            frm2.save()  
  
            messages.success(request, 'Log added successfully.')  
            return redirect('dashboard')  
  
        messages.error(request, 'Please fix issues.')  
        return render(request, 'add_log.html', {  
            'user_log_form': frm, 'food_formset': frm2  
        })  
  
class EditProfileView(LoginRequiredMixin, View):  
    def get(self, request):  
        up, _ = UserProfile.objects.get_or_create(user=request.user)  
        return render(request, 'edit_profile.html', {'form': UserProfileForm(instance=up)})  
  
    def post(self, request):  
        up, _ = UserProfile.objects.get_or_create(user=request.user)  
        frm = UserProfileForm(request.POST, request.FILES, instance=up)  
        if frm.is_valid():  
            frm.save()  
            messages.success(request, 'Profile updated.')  
            return redirect('dashboard')  
        messages.error(request, 'Fix errors.')  
        return render(request, 'edit_profile.html', {'form': frm})  
  
@login_required  
def send_message(request):  
    if request.method == 'POST':  
        frm = MessageForm(request.POST)  
        if frm.is_valid():  
            m = frm.save(commit=False)  
            m.sender = request.user  
            m.save()  
            messages.success(request, 'Message sent.')  
            return redirect('inbox')  
    else:  
        frm = MessageForm()  
    return render(request, 'send_message.html', {'form': frm})  
  
@login_required  
def inbox(request):  
    ms = Message.objects.filter(receiver=request.user).order_by('-timestamp')  
    return render(request, 'inbox.html', {'messages': ms})  
  
@login_required  
def message_detail(request, message_id):  
    obj = get_object_or_404(Message, id=message_id, receiver=request.user)  
    obj.read = True  
    obj.save()  
    return render(request, 'message_detail.html', {'message': obj})  
  
@login_required  
def trainer_dashboard(request):  
    try:  
        tr = Trainer.objects.get(user=request.user)  
    except Trainer.DoesNotExist:  
        tr = None  
    if request.method == 'POST':  
        f = TrainerForm(request.POST, instance=tr)  
        if f.is_valid():  
            temp = f.save(commit=False)  
            temp.user = request.user  
            temp.save()  
            messages.success(request, 'Trainer updated.')  
            return redirect('trainer_dashboard')  
    else:  
        f = TrainerForm(instance=tr)  
    return render(request, 'trainer_dashboard.html', {'form': f, 'trainer': tr})  
  
@login_required  
def create_meal_plan(request):  
    if request.method == 'POST':  
        mp_form = MealPlanForm(request.POST)  
        if mp_form.is_valid():  
            mp = mp_form.save(commit=False)  
            mp.user = request.user  
            mp.save()  
            fs = MealItemFormSet(request.POST, instance=mp)  
            if fs.is_valid():  
                fs.save()  
                messages.success(request, 'MealPlan created.')  
                return redirect('dashboard')  
            else:  
                return render(request, 'create_meal_plan.html', {  
                    'meal_plan_form': mp_form, 'meal_item_formset': fs  
                })  
        else:  
            fs = MealItemFormSet(request.POST)  
            return render(request, 'create_meal_plan.html', {  
                'meal_plan_form': mp_form, 'meal_item_formset': fs  
            })  
    else:  
        mp_form = MealPlanForm()  
        fs = MealItemFormSet()  
        return render(request, 'create_meal_plan.html', {  
            'meal_plan_form': mp_form, 'meal_item_formset': fs  
        })  
  
@method_decorator(csrf_exempt, name='dispatch')  
class WeightPredictionAPI(View):  
    def post(self, request):  
        cal = float(request.POST.get('calories', 0))  
        it = int(request.POST.get('workout_intensity', 1))  
        st = float(request.POST.get('steps', 0))  
        sl = float(request.POST.get('sleep_hours', 0))  
        hr = float(request.POST.get('heart_rate', 0))  
        logs = UserLog.objects.filter(user=request.user)  
        df = pd.DataFrame(list(logs.values()))  
        if df.empty or len(df) < 5:  
            return JsonResponse({'error': 'Not enough data'})  
        X = df[['calories_consumed', 'workout_intensity', 'steps', 'sleep_hours', 'heart_rate']]  
        y = df['weight']  
        model = LinearRegression()  
        model.fit(X, y)  
        fdf = pd.DataFrame([{  
            'calories_consumed': cal,  
            'workout_intensity': it,  
            'steps': st,  
            'sleep_hours': sl,  
            'heart_rate': hr  
        }])  
        pred = model.predict(fdf)  
        return JsonResponse({'predicted_weight': round(float(pred[0]), 2)})  
  
@method_decorator(csrf_exempt, name='dispatch')  
class CalorieEstimationAPI(View):  
    def post(self, request):  
        txt = request.POST.get('food_items', '')  
        fdict = {}  
        for chunk in txt.split(','):  
            try:  
                nm, q = chunk.split(':')  
                fdict[nm.strip()] = float(q.strip())  
            except:  
                pass  
        total = 0  
        macros = {'Protein': 0, 'Fat': 0, 'Carbs': 0}  
        for n, q in fdict.items():  
            try:  
                fi = FoodItem.objects.get(name__iexact=n)  
                factor = q / fi.serving_size  
                total += factor * fi.calories  
                macros['Protein'] += factor * fi.protein  
                macros['Fat'] += factor * fi.fat  
                macros['Carbs'] += factor * fi.carbs  
            except:  
                pass  
        return JsonResponse({  
            'total_calories': round(total, 2),  
            'macronutrients': {  
                'protein': round(macros['Protein'], 2),  
                'fat': round(macros['Fat'], 2),  
                'carbs': round(macros['Carbs'], 2)  
            }  
        })  
  
@login_required  
def export_csv(request):  
    logs = UserLog.objects.filter(user=request.user)  
    resp = HttpResponse(content_type='text/csv')  
    resp['Content-Disposition'] = f'attachment; filename={request.user.username}_logs_{datetime.now().strftime("%Y%m%d")}.csv'  
    w = csv.writer(resp)  
    w.writerow(["Date", "Weight", "Calories", "Intensity", "Steps", "Sleep", "Mood", "HeartRate", "BP", "FoodItems"])  
    for lg in logs:  
        fc = FoodConsumption.objects.filter(user_log=lg)  
        items_str = ', '.join([f"{x.food_item.name}({x.quantity}g)" for x in fc]) if fc else '-'  
        w.writerow([  
            lg.date, lg.weight, lg.calories_consumed, lg.get_workout_intensity_display(),  
            lg.steps, lg.sleep_hours, lg.mood or '-', lg.heart_rate, lg.blood_pressure or '-', items_str  
        ])  
    return resp  
  
@login_required  
def export_pdf(request):  
    logs = UserLog.objects.filter(user=request.user)  
    resp = HttpResponse(content_type='application/pdf')  
    resp['Content-Disposition'] = f'attachment; filename={request.user.username}_logs_{datetime.now().strftime("%Y%m%d")}.pdf'  
    p = canvas.Canvas(resp, pagesize=letter)  
    width, height = letter  
    y = height - 50  
    p.setFont("Helvetica-Bold", 14)  
    p.drawString(50, y, f"User Logs for {request.user.username}")  
    y -= 30  
    p.setFont("Helvetica", 12)  
    headers = ["Date", "Weight", "Calories", "Intensity", "Steps", "Sleep", "Mood", "HeartRate", "BP", "FoodItems"]  
    x_pos = [50, 100, 160, 220, 280, 340, 400, 460, 520, 580]  
    for idx, h in enumerate(headers):  
        p.drawString(x_pos[idx], y, h)  
    y -= 20  
    for lg in logs:  
        if y < 50:  
            p.showPage()  
            y = height - 50  
            p.setFont("Helvetica", 12)  
        fc = FoodConsumption.objects.filter(user_log=lg)  
        items = ', '.join([f"{x.food_item.name}({x.quantity}g)" for x in fc]) if fc else '-'  
        row = [  
            str(lg.date),  
            str(lg.weight),  
            str(lg.calories_consumed),  
            lg.get_workout_intensity_display(),  
            str(lg.steps),  
            str(lg.sleep_hours),  
            lg.mood or '-',  
            str(lg.heart_rate),  
            lg.blood_pressure or '-',  
            items  
        ]  
        for i, v in enumerate(row):  
            p.drawString(x_pos[i], y, v)  
        y -= 20  
    p.save()  
    return resp  
  
def calorie_forecast_sarima(request):  
    # Fetch data from UserLog  
    logs = UserLog.objects.filter(user=request.user).values('date', 'calories_consumed')  
    df = pd.DataFrame(list(logs))  
      
    if df.empty or len(df) < 4:  
        logger.warning("Not enough data for SARIMA forecast.")  
        return None, None  
      
    # Process dates  
    df['date'] = pd.to_datetime(df['date'], errors='coerce')  
    df.dropna(subset=['date'], inplace=True)  
    if df.empty:  
        logger.warning("No valid dates found.")  
        return None, None  
      
    df.set_index('date', inplace=True)  
    df.sort_index(inplace=True)  
      
    if 'calories_consumed' not in df.columns:  
        logger.error("Missing 'calories_consumed' column.")  
        return None, None  
      
    # Resample to daily and fill missing values  
    series = df['calories_consumed'].resample('D').sum()  
    series = series.interpolate(method='time').fillna(method='ffill')  
      
    # Split into train and test  
    train_size = int(len(series) * 0.8)  
    train, test = series[:train_size], series[train_size:]  
      
    # Fit auto_arima  
    try:  
        step_model = auto_arima(train, start_p=1, start_q=1, max_p=5, max_q=5, m=7,  
                                seasonal=True, d=None, D=1, trace=False,  
                                error_action='ignore', suppress_warnings=True,  
                                stepwise=True, n_jobs=-1)  
    except Exception as e:  
        logger.error(f"Error in auto_arima: {e}")  
        return None, None  
      
    # Fit SARIMA model  
    try:  
        sarima = SARIMAX(train, order=step_model.order, seasonal_order=step_model.seasonal_order,  
                         enforce_stationarity=False, enforce_invertibility=False)  
        fitmodel = sarima.fit(disp=False)  
    except Exception as e:  
        logger.error(f"Error fitting SARIMA model: {e}")  
        return None, None  
      
    # Forecast  
    fc_steps = 7  
    forecast = fitmodel.get_forecast(steps=fc_steps)  
    pred = forecast.predicted_mean  
    conf = forecast.conf_int()  
      
    # Calculate errors  
    if len(test) >= fc_steps:  
        mae = mean_absolute_error(test[-fc_steps:], pred)  
        mse = mean_squared_error(test[-fc_steps:], pred)  
        rmse = np.sqrt(mse)  
        logger.info(f"SARIMA Forecast - MAE: {mae:.2f}, RMSE: {rmse:.2f}")  
    else:  
        logger.warning("Not enough test data for error calculation.")  
      
    # Generate plot  
    plot_path = None  
    try:  
        plt.figure(figsize=(10, 5))  
        plt.plot(train.index, train, label='Training Data')  
        plt.plot(test.index, test, label='Actual Data')  
        plt.plot(pred.index, pred, label='Forecast', linestyle='--')  
        plt.fill_between(pred.index, conf.iloc[:, 0], conf.iloc[:, 1], alpha=0.3)  
        plt.title('Calorie Consumption Forecast')  
        plt.xlabel('Date')  
        plt.ylabel('Calories')  
        plt.legend()  
          
        # Save plot  
        save_dir = os.path.join(settings.BASE_DIR, 'monitoring_app/static/images')  
        os.makedirs(save_dir, exist_ok=True)  
        plot_path = os.path.join(save_dir, 'calorie_forecast.png')  
        plt.savefig(plot_path)  
        plt.close()  
    except Exception as e:  
        logger.error(f"Error generating forecast plot: {e}")  
      
    return pred, plot_path  