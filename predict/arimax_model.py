# -*- coding: utf-8 -*-
"""
ARIMAX 模型（需求文档 8.3）：SARIMAX + 饲料价格外生变量
  - align_exog: 主序列与饲料序列按日期对齐（重采样+插值）
  - forecast_exog: 外生变量未来值线性外推
  - fit_forecast: 拟合 + 预测含置信区间
"""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# 季节周期：政府数据多为周度，s=7 对应一周的季节性；日度数据同样可用
SEASONAL_PERIOD = 7


def align_exog(series: pd.Series, exog_series: pd.Series):
    """
    主序列（牛羊价）与外生序列（饲料价）对齐到同一日频索引
    缺失日线性插值
    """
    idx = series.index.union(exog_series.index)
    y = series.reindex(idx).interpolate().ffill().bfill()
    x = exog_series.reindex(idx).interpolate().ffill().bfill()
    return y, x


def forecast_exog(x: pd.Series, days: int) -> pd.Series:
    """
    外生变量未来 days 天取值：用最近 14 天的线性趋势外推
    （玉米豆粕短期走势平缓，线性外推足够；避免复杂化）
    """
    window = x.tail(14)
    if len(window) < 2 or window.nunique() == 1:
        return pd.Series([x.iloc[-1]] * days)       # 无趋势：保持不变
    slope = np.polyfit(np.arange(len(window)), window.values, 1)[0]
    future = [x.iloc[-1] + slope * (i + 1) for i in range(days)]
    future = [max(v, 0.0) for v in future]          # 价格不为负
    return pd.Series(future)


def fit_forecast(series: pd.Series, exog_series: pd.Series, days=30,
                 order=(1, 1, 1)):
    """
    拟合 SARIMAX(series ~ exog) 并预测 days 天
    返回 (预测DataFrame, 实际使用的order)
    """
    y, x = align_exog(series, exog_series)

    model = SARIMAX(
        y,
        exog=x,
        order=order,
        seasonal_order=(1, 0, 0, SEASONAL_PERIOD),   # 轻度季节项，防周度数据锯齿
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    result = model.fit(disp=False)

    x_future = forecast_exog(x, days)
    forecast = result.get_forecast(steps=days, exog=x_future.values.reshape(-1, 1))
    mean = forecast.predicted_mean
    ci = forecast.conf_int(alpha=0.05)

    out = pd.DataFrame({
        "mean": mean.values,
        "lower": ci.iloc[:, 0].values,
        "upper": ci.iloc[:, 1].values,
    }, index=pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=days))
    return out, order
