from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserLogViewSet, UserProfileViewSet, MessageViewSet, MealPlanViewSet

router = DefaultRouter()
router.register(r'userlogs', UserLogViewSet, basename='userlog')
router.register(r'userprofiles', UserProfileViewSet, basename='userprofile')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'mealplans', MealPlanViewSet, basename='mealplan')

urlpatterns = [
    path('', include(router.urls)),
]