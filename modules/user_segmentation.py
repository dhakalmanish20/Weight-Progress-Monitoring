import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import matplotlib.pyplot as plt

def user_segmentation(user_logs):
    data = pd.DataFrame(list(user_logs.values()))
    if data.empty or len(data) < 2:
        print("Not enough data for clustering.")
        return
    data['BMI'] = data['weight'] / (1.75 ** 2)
    features = data[['BMI', 'workout_intensity', 'calories_consumed']]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    kmeans = KMeans(n_clusters=3, random_state=42)
    data['Cluster'] = kmeans.fit_predict(scaled_features)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=data, x='BMI', y='workout_intensity', hue='Cluster', palette='viridis', s=100)
    plt.title('User Segmentation (K-Means Clustering)')
    plt.xlabel('BMI')
    plt.ylabel('Workout Intensity')
    plt.legend(title='Cluster')
    plt.grid()
    plt.savefig('monitoring_app/static/images/user_clusters.png')
    plt.close()