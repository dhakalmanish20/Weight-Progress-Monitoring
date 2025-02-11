import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')

def fitness_trend_prediction(user_logs, calories, workout_intensity):
    data = pd.DataFrame(list(user_logs.values()))
    if data.empty or len(data) < 2:
        print("Not enough data for prediction.")
        return
    X = data[['calories_consumed', 'workout_intensity']]
    y = data['weight']
    model = LinearRegression()
    model.fit(X, y)
    future_data = pd.DataFrame({
        'calories_consumed': [calories],
        'workout_intensity': [workout_intensity]
    })
    future_weight = model.predict(future_data)

    plt.figure(figsize=(10, 6))
    plt.plot(data['date'], data['weight'], label='Historical Weight', marker='o')
    plt.plot([data['date'].iloc[-1] + pd.Timedelta(days=1)], future_weight, label='Predicted Weight', marker='o', linestyle='--')
    plt.xlabel('Date')
    plt.ylabel('Weight (kg)')
    plt.title('Weight Trend Prediction')
    plt.legend()
    plt.grid()
    plt.savefig('monitoring_app/static/images/weight_trend.png')
    plt.close()