from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitoring_app.urls')),  # Root URL maps directly to app URLs, no namespace
    path('api/', include('api.urls')),
    path('accounts/', include(('weight_monitoring.urls_two_factor', 'two_factor'), namespace='two_factor')),  # Keep 2FA namespace
    path('captcha/', include('captcha.urls')),
    path('', include('django.contrib.auth.urls')),  # Add this line to include auth URLs
]