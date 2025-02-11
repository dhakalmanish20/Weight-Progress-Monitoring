from django.urls import path
from .views import (
    IndexView, CustomLoginView, logout_view, RegisterView, DashboardView,
    AddLogView, EditProfileView, send_message, inbox, message_detail,
    WeightPredictionAPI, CalorieEstimationAPI, export_csv, export_pdf,
    trainer_dashboard, create_meal_plan
)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('add_log/', AddLogView.as_view(), name='add_log'),
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),
    path('send_message/', send_message, name='send_message'),
    path('inbox/', inbox, name='inbox'),
    path('message/<int:message_id>/', message_detail, name='message_detail'),
    path('weight_prediction_api/', WeightPredictionAPI.as_view(), name='weight_prediction_api'),
    path('calorie_estimation_api/', CalorieEstimationAPI.as_view(), name='calorie_estimation_api'),
    path('export_csv/', export_csv, name='export_csv'),
    path('export_pdf/', export_pdf, name='export_pdf'),
    path('trainer_dashboard/', trainer_dashboard, name='trainer_dashboard'),
    path('create_meal_plan/', create_meal_plan, name='create_meal_plan'),
]