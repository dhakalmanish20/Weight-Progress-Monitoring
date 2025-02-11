# monitoring_app/analysis/time_series.py
import os
import pandas as pd  
import numpy as np  
import matplotlib.pyplot as plt  
from statsmodels.tsa.statespace.sarimax import SARIMAX  
from pmdarima import auto_arima  
from sklearn.metrics import mean_absolute_error, mean_squared_error  
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf  
import warnings  
warnings.filterwarnings('ignore')  
import logging  
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  

def calorie_forecast_sarima(log_queryset):  
    """  
    Returns 7-day forecast of daily calorie consumption using SARIMA.  
    """  
    df = pd.DataFrame(list(log_queryset.values()))  
    if df.empty or len(df) < 15:  
        logger.warning("Not enough data for SARIMA.")  
        return None  
    if 'date' not in df.columns:  
        return None  
    df['date'] = pd.to_datetime(df['date'])  
    df.set_index('date', inplace=True)  
    df.sort_index(inplace=True)  
    series = df['calories_consumed'].resample('D').sum().fillna(method='ffill')  
    train_size = int(len(series) * 0.8)  
    train, test = series[:train_size], series[train_size:]  
    step_model = auto_arima(train, start_p=1, start_q=1, max_p=5, max_q=5, m=7, seasonal=True,    
                            d=None, D=1, trace=False, error_action='ignore',  
                            suppress_warnings=True, stepwise=True,   
                            n_jobs=-1)  
    sarima = SARIMAX(train, order=step_model.order, seasonal_order=step_model.seasonal_order,  
                     enforce_stationarity=False, enforce_invertibility=False)  
    fitmodel = sarima.fit(disp=False)  
    fc_steps = 7  
    forecast = fitmodel.get_forecast(steps=fc_steps)  
    pred = forecast.predicted_mean  
    conf = forecast.conf_int()  
    mae = mean_absolute_error(test[:fc_steps], pred[:len(test[:fc_steps])])  
    mse = mean_squared_error(test[:fc_steps], pred[:len(test[:fc_steps])])  
    rmse = np.sqrt(mse)  
    logger.info(f"SARIMA: mae={mae:.2f}, rmse={rmse:.2f}")  
    try:  
        plt.figure(figsize=(10, 5))  
        plt.plot(train.index, train, label='Train', color='blue')  
        plt.plot(test.index, test, label='Test', color='green')  
        idx = pred.index  
        plt.plot(idx, pred, label='Forecast', color='red', ls='--')  
        plt.fill_between(idx, conf.iloc[:, 0], conf.iloc[:, 1], alpha=0.3, color='gray')  
        plt.title("Daily Calorie Forecast (SARIMA)")  
        plt.legend()  
        os.makedirs('monitoring_app/static/images', exist_ok=True)  
        plt.savefig('monitoring_app/static/images/calorie_forecast_sarima.png')  
        plt.close()  
    except Exception as e:  
        logger.error(f"Error while plotting: {e}")  
    return pred  