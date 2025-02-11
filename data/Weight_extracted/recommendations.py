import pandas as pd
from sklearn.neighbors import NearestNeighbors
from monitoring_app.models import UserProfile, UserLog

def get_recommendations(user):
    user_profile = UserProfile.objects.get(user=user)
    user_logs = UserLog.objects.filter(user=user)
    data = pd.DataFrame(list(user_logs.values()))

    if data.empty or len(data) < 5:
        return ['Please log more data to receive personalized recommendations.']

    features = ['calories_consumed', 'workout_intensity', 'steps', 'sleep_hours', 'heart_rate']
    data = data[features]
    data['user_id'] = user.id

    other_user_logs = UserLog.objects.exclude(user=user)
    if not other_user_logs.exists():
        return ['No recommendations available at this time.']

    other_data = pd.DataFrame(list(other_user_logs.values()))
    other_data = other_data[features]
    other_data['user_id'] = other_user_logs.values_list('user', flat=True)

    combined_data = pd.concat([data, other_data], ignore_index=True)
    combined_data = combined_data.dropna()
    combined_features = combined_data[features]

    nn = NearestNeighbors(n_neighbors=5, algorithm='ball_tree')
    nn.fit(combined_features)

    distances, indices = nn.kneighbors([data[features].mean()])
    similar_users_ids = combined_data.iloc[indices[0]]['user_id'].unique()

    recommendations = []
    for uid in similar_users_ids:
        if uid != user.id:
            profile = UserProfile.objects.get(user_id=uid)
            recommendations.append(f"Consider adjusting your target weight to {profile.target_weight} kg like user {profile.user.username}.")

    if not recommendations:
        recommendations.append("Keep up the good work!")

    return recommendations