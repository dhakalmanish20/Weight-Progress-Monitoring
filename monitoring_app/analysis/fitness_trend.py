import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

def predict_weight_trend(dates, weights):
    if not dates or not weights or len(dates) < 2:
        return [], 0.0

    # Convert dates to numerical indices for Linear Regression
    X = np.array(range(len(dates))).reshape(-1, 1)
    y = np.array(weights)

    # Fit Linear Regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next 7 days
    future_days = 7
    future_X = np.array(range(len(dates), len(dates) + future_days)).reshape(-1, 1)
    predicted_weights = model.predict(future_X)

    # Generate prediction dates
    prediction_dates = [(datetime.now().date() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(future_days)]

    # Return pairs of (date, weight) and confidence score
    predictions = list(zip(prediction_dates, predicted_weights.tolist()))
    confidence = model.score(X, y)  # R^2 score as confidence

    return predictions, confidence