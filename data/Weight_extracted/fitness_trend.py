import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os

def fitness_trend_prediction(user_logs, calories, workout_intensity, steps, sleep_hours, heart_rate):
    data = pd.DataFrame(list(user_logs.values()))
    if data.empty or len(data) < 5:
        print("Not enough data for prediction.")
        return
    features = ['calories_consumed', 'workout_intensity', 'steps', 'sleep_hours', 'heart_rate']
    target = 'weight'
    X = data[features]
    y = data[target]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = keras.Sequential([
        keras.layers.Dense(64, activation='relu', input_shape=(X_scaled.shape[1],)),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_scaled, y, epochs=100, verbose=0)

    future_data = pd.DataFrame({
        'calories_consumed': [calories],
        'workout_intensity': [workout_intensity],
        'steps': [steps],
        'sleep_hours': [sleep_hours],
        'heart_rate': [heart_rate]
    })
    future_scaled = scaler.transform(future_data)
    future_weight = model.predict(future_scaled)

    model.save('fitness_trend_model.h5')

    plt.figure(figsize=(10, 6))
    plt.plot(data['date'], data['weight'], label='Historical Weight', marker='o')
    plt.plot([data['date'].iloc[-1] + pd.Timedelta(days=1)], future_weight, label='Predicted Weight', marker='o', linestyle='--')
    plt.xlabel('Date')
    plt.ylabel('Weight (kg)')
    plt.title('Weight Trend Prediction')
    plt.legend()
    plt.grid()
    os.makedirs('monitoring_app/static/images', exist_ok=True)
    plt.savefig('monitoring_app/static/images/weight_trend.png')
    plt.close()