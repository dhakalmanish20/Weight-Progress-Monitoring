import numpy as np
from scipy.stats import linregress, norm
from scipy.signal import savgol_filter
from datetime import datetime, timedelta
from monitoring_app.models import WeightLog
import pandas as pd

class CustomAccurateFitnessAlgorithms:
    @staticmethod
    def preprocess_data(weights):
        """
        Preprocess weight data: smooth, normalize, and remove outliers.
        """
        if len(weights) < 3:
            return weights, 0, 1

        # Smooth data with Savitzky-Golay filter
        window_length = min(5, len(weights))
        smoothed = savgol_filter(weights, window_length=window_length, polyorder=2)

        # Remove outliers using IQR
        q1, q3 = np.percentile(smoothed, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.0 * iqr
        upper_bound = q3 + 1.0 * iqr
        cleaned = [w for w in smoothed if lower_bound <= w <= upper_bound]

        if not cleaned:
            return weights, 0, 1

        mean_weight = np.mean(cleaned)
        std_weight = np.std(cleaned) if np.std(cleaned) > 0 else 1.0
        normalized = [(w - mean_weight) / std_weight for w in cleaned]

        return normalized, mean_weight, std_weight

    @staticmethod
    def predict_future_weights(user_id, days_ahead=7):
        """
        Predict future weights using linear regression.

        Args:
            user_id (int): The ID of the user.
            days_ahead (int): Number of days to predict ahead.

        Returns:
            tuple: (list of (date, predicted_weight, lower_bound, upper_bound) tuples, accuracy_score)
        """
        try:
            logs = WeightLog.objects.filter(user_id=user_id).order_by('date')
            dates = [log.date for log in logs]
            weights = [log.weight for log in logs]

            if len(dates) < 3:
                return [], 0.0

            # Preprocess data
            normalized_weights, mean_weight, std_weight = CustomAccurateFitnessAlgorithms.preprocess_data(weights)

            if not normalized_weights:
                return [], 0.0

            # Fit linear regression
            X = np.array(range(len(normalized_weights)))
            y = np.array(normalized_weights)

            slope, intercept, r_value, p_value, std_err = linregress(X, y)

            # Predict future
            future_X = np.array(range(len(normalized_weights), len(normalized_weights) + days_ahead))
            predicted_normalized = slope * future_X + intercept

            # Inverse normalize
            predicted_weights = [p * std_weight + mean_weight for p in predicted_normalized]

            # Estimate bounds using standard error
            residual_std = std_err * 1.5
            lower_bounds = predicted_normalized - 2 * residual_std
            upper_bounds = predicted_normalized + 2 * residual_std

            # Inverse normalize bounds
            lower_bounds = [lb * std_weight + mean_weight for lb in lower_bounds]
            upper_bounds = [ub * std_weight + mean_weight for ub in upper_bounds]

            # Generate prediction dates
            prediction_dates = [(dates[-1] + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(days_ahead)]

            # Return predictions with bounds
            predictions = list(zip(prediction_dates, predicted_weights, lower_bounds, upper_bounds))

            # Accuracy score (R²)
            accuracy_score = r_value ** 2

            return predictions, accuracy_score

        except Exception as e:
            print(f"Prediction error: {e}")
            return [], 0.0

    @staticmethod
    def segment_users_adaptive_clustering(user_ids, variance_threshold=0.7, stability_factor=0.15):
        """
        Segment users using adaptive clustering based on weight variance.

        Args:
            user_ids (list): List of user IDs.
            variance_threshold (float): Maximum variance for clustering.
            stability_factor (float): Factor for cluster stability.

        Returns:
            dict: Mapping of user IDs to cluster labels, with outliers marked as -1.
        """
        try:
            all_data = []
            user_map = {}

            for i, user_id in enumerate(user_ids):
                weights = [log.weight for log in WeightLog.objects.filter(user_id=user_id).order_by('date')]
                if weights and len(weights) > 2:
                    cleaned, _, _ = CustomAccurateFitnessAlgorithms.preprocess_data(weights)
                    if cleaned:
                        mean_weight = np.mean(cleaned)
                        variance_weight = np.var(cleaned)
                        if variance_weight <= variance_threshold:
                            all_data.append([mean_weight, variance_weight])
                            user_map[len(all_data) - 1] = user_id

            if len(all_data) < 2:
                return {}

            # Adaptive clustering
            clusters = {}
            current_cluster = 0
            sorted_data = sorted(all_data, key=lambda x: x[1])  # Sort by variance

            for i, (mean, variance) in enumerate(sorted_data):
                if i == 0 or (sorted_data[i-1][1] - variance) / max(variance, 1e-10) > stability_factor:
                    current_cluster += 1
                clusters[user_map[i]] = current_cluster

            # Outlier detection using z-score
            means = np.array([d[0] for d in all_data])
            std_all = np.std(means) if np.std(means) > 0 else 1.0

            for user_id in user_ids:
                if user_id not in clusters:
                    weights = [log.weight for log in WeightLog.objects.filter(user_id=user_id).order_by('date')]
                    if weights and len(weights) > 2:
                        cleaned, mean_weight, _ = CustomAccurateFitnessAlgorithms.preprocess_data(weights)
                        if cleaned:
                            z_score = (mean_weight - np.mean(means)) / std_all
                            if abs(z_score) > 2.0:
                                clusters[user_id] = -1
                            else:
                                clusters[user_id] = current_cluster + 1

            return clusters

        except Exception as e:
            print(f"Clustering error: {e}")
            return {}

    @staticmethod
    def forecast_weights_ensemble(user_id, steps=7, ensemble_size=15, trend_sensitivity=0.2):
        """
        Forecast future weights using a stable ensemble of trend analysis, ensuring consistent array sizes.

        Args:
            user_id (int): The ID of the user.
            steps (int): Number of future steps to forecast.
            ensemble_size (int): Number of models in the ensemble.
            trend_sensitivity (float): Sensitivity to recent trends.

        Returns:
            list: Ensemble-averaged forecasted weight values.
        """
        try:
            weights = [log.weight for log in WeightLog.objects.filter(user_id=user_id).order_by('date')]

            if len(weights) < 3:
                return []

            # Preprocess
            cleaned, mean_weight, std_weight = CustomAccurateFitnessAlgorithms.preprocess_data(weights)
            if not cleaned:
                return []

            forecasts = []
            for _ in range(ensemble_size):
                # Weighted moving average
                weights_recent = np.exp(-np.arange(len(cleaned)) * trend_sensitivity)
                smoothed = np.average(cleaned, weights=weights_recent[::-1], axis=0)

                # Linear trend extrapolation
                X = np.array(range(len(cleaned)))
                y = np.array(smoothed)
                slope, intercept, _, _, _ = linregress(X, y)
                last_x = len(cleaned) - 1

                # Ensure all forecasts have the same length (steps)
                forecast = [intercept + slope * (last_x + i) for i in range(steps)]
                forecasts.append(forecast)

            # Pad or truncate all forecasts to ensure same length (steps)
            max_len = steps  # Fixed length for all forecasts
            padded_forecasts = [f[:max_len] for f in forecasts]  # Truncate to steps

            # Ensemble average
            ensemble_forecast_normalized = np.mean(padded_forecasts, axis=0).tolist()

            # Inverse normalize
            final_forecast = [f * std_weight + mean_weight for f in ensemble_forecast_normalized]

            return final_forecast

        except Exception as e:
            print(f"Forecast error: {e}")
            return []