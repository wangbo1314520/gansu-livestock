# -*- coding: utf-8 -*-
"""
预测评价（需求文档 8.4）：MAE / RMSE / MAPE 与回测
  MAPE <10% 优秀，<20% 良好
"""
import numpy as np


def mae(y_true, y_pred) -> float:
    """平均绝对误差"""
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    """均方根误差"""
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true, y_pred) -> float:
    """平均绝对百分比误差（%）；真实值接近0的样本剔除"""
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) > 1e-8
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def all_metrics(y_true, y_pred) -> dict:
    """一次算三个指标，统一保留4位小数"""
    return {
        "mae": round(mae(y_true, y_pred), 4),
        "rmse": round(rmse(y_true, y_pred), 4),
        "mape": round(mape(y_true, y_pred), 4),
    }


def grade(mape_value: float) -> str:
    """MAPE 分级：<10% 优秀，<20% 良好，其余一般"""
    if np.isnan(mape_value):
        return "无数据"
    if mape_value < 10:
        return "优秀"
    if mape_value < 20:
        return "良好"
    return "一般"


def backtest(forecast_fn, s, test_days=30):
    """
    简单回测：最后 test_days 天作为测试集，之前的数据训练
      forecast_fn(train_series) -> 预测值数组（长度 test_days）
    返回 {mae, rmse, mape, grade}
    """
    if len(s) < test_days + 30:
        return None                       # 数据太少不回测
    train, test = s[:-test_days], s[-test_days:]
    pred = forecast_fn(train)
    metrics = all_metrics(test.values, pred)
    metrics["grade"] = grade(metrics["mape"])
    return metrics
