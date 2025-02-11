# weight_monitoring/urls.py
from django.contrib import admin  
from django.urls import path, include  
import weight_monitoring.urls_two_factor  

urlpatterns = [  
    path('admin/', admin.site.urls),  
    path('', include('monitoring_app.urls')),  
    path('api/', include('api.urls')),  
    path('accounts/', include(('weight_monitoring.urls_two_factor','two_factor'), namespace='two_factor')),  
    path('captcha/', include('captcha.urls')),  
]  