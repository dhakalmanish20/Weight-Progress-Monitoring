from statistics import LinearRegression
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from datetime import datetime, timedelta
from monitoring_app.models import WeightLog

class CustomFitnessAlgorithms:
    @staticmethod
    def predict_future_weights(user_id, days_ahead=7):
        """
        Predict future weights for a user using Linear Regression on historical data.

        Args:
            user_id (int): The ID of the user.
            days_ahead (int): Number of days to predict ahead.

        Returns:
            tuple: (list of (date, predicted_weight) pairs, confidence score)
        """
        try:
            logs = WeightLog.objects.filter(user_id=user_id).order_by('date')
            dates = [log.date for log in logs]
            weights = [log.weight for log in logs]

            if len(dates) < 2:
                return [], 0.0

            # Convert dates to numerical indices
            X = np.array(range(len(dates))).reshape(-1, 1)
            y = np.array(weights)

            # Fit Linear Regression
            model = LinearRegression()
            model.fit(X, y)

            # Predict future
            future_X = np.array(range(len(dates), len(dates) + days_ahead)).reshape(-1, 1)
            predicted_weights = model.predict(future_X)

            # Generate prediction dates
            prediction_dates = [(dates[-1] + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(days_ahead)]

            # Return predictions and confidence (R^2)
            predictions = list(zip(prediction_dates, predicted_weights.tolist()))
            confidence = model.score(X, y)

            return predictions, confidence

        except Exception as e:
            print(f"Prediction error: {e}")
            return [], 0.0

    @staticmethod
    def segment_users_by_weight(user_ids, n_clusters=3):
        """
        Segment users based on their weight trends using Hierarchical Clustering.

        Args:
            user_ids (list): List of user IDs.
            n_clusters (int): Number of clusters.

        Returns:
            dict: Mapping of user IDs to cluster labels.
        """
        try:
            all_weights = []
            user_map = {}

            # Collect weight data for all users
            for i, user_id in enumerate(user_ids):
                weights = [log.weight for log in WeightLog.objects.filter(user_id=user_id).order_by('date')]
                if weights:
                    all_weights.append(np.mean(weights))  # Use mean weight as feature
                    user_map[i] = user_id

            if not all_weights:
                return {}

            # Hierarchical Clustering
            clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
            clusters = clustering.fit_predict(np.array(all_weights).reshape(-1, 1))

            # Map clusters back to user IDs
            result = {user_map[i]: cluster for i, cluster in enumerate(clusters)}
            return result

        except Exception as e:
            print(f"Segmentation error: {e}")
            return {}

    @staticmethod
    def forecast_weights_exponential(user_id, steps=7):
        """
        Forecast future weights using Exponential Smoothing.

        Args:
            user_id (int): The ID of the user.
            steps (int): Number of future steps to forecast.

        Returns:
            list: Forecasted weight values.
        """
        try:
            weights = [log.weight for log in WeightLog.objects.filter(user_id=user_id).order_by('date')]

            if len(weights) < 2:
                return []

            # Fit Exponential Smoothing model
            model = ExponentialSmoothing(weights, trend='add', seasonal=None, seasonal_periods=None)
            fit = model.fit()

            # Forecast
            forecast = fit.forecast(steps).tolist()
            return forecast

        except Exception as e:
            print(f"Forecast error: {e}")
            return []