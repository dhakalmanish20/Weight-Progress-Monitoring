# monitoring_app/analysis/__init__.py
from .custom_algorithms import CustomAccurateFitnessAlgorithms  # New algorithms

__all__ = ['predict_weight_trend', 'forecast_time_series', 'segment_users', 'CustomFitnessAlgorithms']