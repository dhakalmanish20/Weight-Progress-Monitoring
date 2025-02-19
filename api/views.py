from rest_framework import viewsets, serializers
from monitoring_app.models import WeightLog, UserProfile, Message, MealPlan
from django.contrib.auth.models import User

class UserLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog  # Changed from UserLog to WeightLog
        fields = ['id', 'user', 'date', 'weight', 'calories_consumed', 'workout_intensity', 'steps', 'sleep_hours', 'heart_rate', 'blood_pressure', 'mood']

class UserLogViewSet(viewsets.ModelViewSet):
    serializer_class = UserLogSerializer

    def get_queryset(self):
        return WeightLog.objects.all()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'height', 'target_weight', 'profile_picture']

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.all()

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp']

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.all()

class MealPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlan
        fields = ['id', 'user', 'name', 'created_at']

class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanSerializer

    def get_queryset(self):
        return MealPlan.objects.all()