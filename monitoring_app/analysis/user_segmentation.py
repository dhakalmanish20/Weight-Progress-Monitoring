# monitoring_app/analysis/user_segmentation.py
import os  
import numpy as np  
import pandas as pd  
import seaborn as sns  
import matplotlib.pyplot as plt  
from sklearn.cluster import KMeans  
from sklearn.preprocessing import StandardScaler  

def cluster_users(log_queryset):  
    """  
    Perform K-Means clustering on user logs based on weight, workout_intensity, and BMI assumptions.  
    """  
    df = pd.DataFrame(list(log_queryset.values()))  
    if df.empty or len(df) < 2:  
        return None  
    if 'weight' not in df.columns:  
        return None  
    df['BMI'] = df['weight'] / (1.75**2)  
    feats = ['BMI','workout_intensity','calories_consumed']  
    df2 = df[feats].dropna()  
    if df2.empty:  
        return None  
    X = StandardScaler().fit_transform(df2)  
    kmeans = KMeans(n_clusters=3, random_state=42)  
    clusters = kmeans.fit_predict(X)  
    df['Cluster'] = clusters  
    if not os.path.exists('monitoring_app/static/images'):  
        os.makedirs('monitoring_app/static/images', exist_ok=True)  
    plt.figure(figsize=(9,6))  
    sns.scatterplot(data=df, x='BMI', y='workout_intensity', hue='Cluster', palette='viridis')  
    plt.title("User Segmentation")  
    plt.savefig('monitoring_app/static/images/user_segmentation.png')  
    plt.close()  
    return clusters  