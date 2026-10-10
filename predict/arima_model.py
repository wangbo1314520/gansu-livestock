# -*- coding: utf-8 -*-
"""
ARIMA 模型（需求文档 8.2）：牛羊价格基础预测
  - auto_order: AIC 网格搜索 (p, d, q)
  - fit_forecast: 拟合 + 预测未来 days 天（含95%置信区间）
"""
import warnings

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

# statsmodels 的收敛警告在批量跑时很吵，只保留错误
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


def auto_order(s: pd.Series, max_p=3, max_d=2, max_q=3):
    """AIC 最小的 (p,d,q)；d 用 ADF 建议，p/q 网格搜索"""
    from predict.preprocess import suggest_d
    d = suggest_d(s, max_d=max_d)

    best_order, best_aic = (1, d, 1), float("inf")
    for p in range(max_p + 1):
        for q in range(max_q + 1):
            try:
                model = ARIMA(s, order=(p, d, q))
                result = model.fit()
                if result.aic < best_aic:
                    best_order, best_aic = (p, d, q), result.aic
            except Exception:
                continue          # 个别阶数不收敛，跳过
    return best_order


def fit_forecast(s: pd.Series, days=30, order=None):
    """
    拟合 ARIMA 并预测 days 天
    返回 DataFrame(index=未来日期, columns=[mean, lower, upper])
    """
    if order is None:
        order = auto_order(s)

    model = ARIMA(s, order=order)
    result = model.fit()
    forecast = result.get_forecast(steps=days)
    mean = forecast.predicted_mean
    ci = forecast.conf_int(alpha=0.05)              # 95% 置信区间

    out = pd.DataFrame({
        "mean": mean.values,
        "lower": ci.iloc[:, 0].values,
        "upper": ci.iloc[:, 1].values,
    }, index=pd.date_range(s.index[-1] + pd.Timedelta(days=1), periods=days))
    return out, order
