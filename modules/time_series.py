import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pmdarima import auto_arima
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
warnings.filterwarnings('ignore')
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def activity_trend_forecast(user_logs):
    try:
        data = pd.DataFrame(list(user_logs.values()))
        logger.info("User logs converted to DataFrame.")

        if data.empty or len(data) < 15:
            logger.warning("Not enough data for time-series forecasting.")
            return

        data['date'] = pd.to_datetime(data['date'])
        data.set_index('date', inplace=True)
        data.sort_index(inplace=True)

        ts_data = data['calories_consumed'].resample('D').sum()
        ts_data = ts_data.fillna(method='ffill')
        logger.info("Data resampled and missing values handled.")

        train_size = int(len(ts_data) * 0.8)
        train, test = ts_data[:train_size], ts_data[train_size:]
        logger.info(f"Data split into training ({len(train)}) and testing ({len(test)}) sets.")

        stepwise_model = auto_arima(train,
                                    start_p=1, start_q=1,
                                    max_p=3, max_q=3,
                                    m=7, seasonal=True,
                                    start_P=0,
                                    d=None, D=1, trace=False,
                                    error_action='ignore',
                                    suppress_warnings=True,
                                    stepwise=True,
                                    n_jobs=-1)

        logger.info(f"Auto ARIMA model selected: Order={stepwise_model.order}, Seasonal Order={stepwise_model.seasonal_order}")

        model = SARIMAX(train,
                        order=stepwise_model.order,
                        seasonal_order=stepwise_model.seasonal_order,
                        enforce_stationarity=False,
                        enforce_invertibility=False)

        model_fit = model.fit(disp=False)
        logger.info("SARIMAX model fitted.")

        forecast_steps = len(test)
        forecast = model_fit.get_forecast(steps=forecast_steps)
        forecast_values = forecast.predicted_mean
        conf_int = forecast.conf_int()

        mae = mean_absolute_error(test, forecast_values)
        mse = mean_squared_error(test, forecast_values)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((test - forecast_values) / test)) * 100

        logger.info(f'Forecast Evaluation Metrics: MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%')

        residuals = model_fit.resid
        fig, ax = plt.subplots(1, 2, figsize=(15, 5))
        plot_acf(residuals, ax=ax[0])
        plot_pacf(residuals, ax=ax[1])
        ax[0].set_title('ACF of Residuals')
        ax[1].set_title('PACF of Residuals')
        diagnostics_image = os.path.join('monitoring_app/static/images', 'activity_diagnostics.png')
        plt.savefig(diagnostics_image)
        plt.close()
        logger.info("Model diagnostics plotted.")

        plt.figure(figsize=(12, 6))
        plt.plot(train.index, train, label='Training Data', color='blue')
        plt.plot(test.index, test, label='Actual Data', color='green')
        plt.plot(forecast_values.index, forecast_values, label='Forecast', color='red', linestyle='--')
        plt.fill_between(forecast_values.index,
                         conf_int.iloc[:, 0],
                         conf_int.iloc[:, 1],
                         color='pink', alpha=0.3, label='Confidence Interval')
        plt.title('Calories Consumed - Time Series Forecast')
        plt.xlabel('Date')
        plt.ylabel('Calories Consumed')
        plt.legend()
        plt.grid(True)

        image_dir = 'monitoring_app/static/images'
        os.makedirs(image_dir, exist_ok=True)
        plt.savefig(os.path.join(image_dir, 'activity_trend.png'))
        plt.close()
        logger.info("Forecast plot saved.")

    except Exception as e:
        logger.exception("An error occurred during time-series forecasting.")