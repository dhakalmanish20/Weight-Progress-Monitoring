# monitoring_app/analysis/fitness_trend.py
import os  
from matplotlib import pyplot as plt
import numpy as np  
import pandas as pd  
import xgboost as xgb  
from sklearn.preprocessing import StandardScaler  
from django.conf import settings  
from sklearn.model_selection import train_test_split  

def advanced_fitness_prediction(log_queryset, calories, intensity, steps, sleep_hrs, heart_rate):  
    df = pd.DataFrame(list(log_queryset.values()))  
    if df.empty or len(df) < 5:  
        return None  
    features = ['calories_consumed', 'workout_intensity', 'steps', 'sleep_hours', 'heart_rate']  
    target = 'weight'  
    df = df.dropna(subset=features + [target])  
    X = df[features]  
    y = df[target]  
    scaler = StandardScaler()  
    X_scaled = scaler.fit_transform(X)  
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)  
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1)  
    model.fit(X_train, y_train)  
    new_data = pd.DataFrame([{  
        'calories_consumed': calories,  
        'workout_intensity': intensity,  
        'steps': steps,  
        'sleep_hours': sleep_hrs,  
        'heart_rate': heart_rate  
    }])  
    new_scaled = scaler.transform(new_data)  
    pred_weight = model.predict(new_scaled)  
    # Optionally save the model if desired  
    model_path = os.path.join(settings.BASE_DIR, 'fitness_trend_model_xgb.json')  
    model.save_model(model_path)  
    return float(pred_weight[0])  

def plot_historical_and_prediction(log_queryset, predicted_val):  
    df = pd.DataFrame(list(log_queryset.values()))  
    if df.empty:  
        return  
    if 'date' not in df.columns:  
        return  
    df['date'] = pd.to_datetime(df['date'])  
    df = df.sort_values('date')  
    plt.figure(figsize=(9, 5))  
    plt.plot(df['date'], df['weight'], marker='o', label='History')  
    if len(df) > 0:  
        next_day = df['date'].iloc[-1] + pd.Timedelta(days=1)  
        plt.plot(next_day, predicted_val, 'ro--', label='Prediction')  
    plt.title("Weight Trend")  
    plt.xlabel("Date")  
    plt.ylabel("Weight (kg)")  
    plt.legend()  
    if not os.path.exists('monitoring_app/static/images'):  
        os.makedirs('monitoring_app/static/images', exist_ok=True)  
    plt.savefig('monitoring_app/static/images/weight_trend_adv.png')  
    plt.close()  