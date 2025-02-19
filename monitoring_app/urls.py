from django.urls import path
from .views import IndexView, dashboard, add_log, edit_profile, login_view, register_view, results, export_csv, export_pdf, send_message

urlpatterns = [
    path('', IndexView.as_view(), name='index'),  # Root pattern
    path('dashboard/', dashboard, name='dashboard'),
    path('add_log/', add_log, name='add_log'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('results/', results, name='results'),
    path('export_csv/', export_csv, name='export_csv'),
    path('export_pdf/', export_pdf, name='export_pdf'),
    path('send_message/', send_message, name='send_message'),  # New URL pattern
]