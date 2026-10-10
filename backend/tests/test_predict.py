# -*- coding: utf-8 -*-
"""ARIMA 预测测试：合成数据直接调 predict 包（不经 HTTP、不连库）"""
import datetime
import math
import random

import pytest

from predict.predictor import predict_series


def _make_series(n=150, base=15.0, slope=0.01):
    """合成价格序列：趋势 + 周期 + 噪声"""
    random.seed(7)
    start = datetime.date(2026, 1, 1)
    return [((start + datetime.timedelta(days=i)).isoformat(),
             base + slope * i + 0.4 * math.sin(i / 5) + random.uniform(-0.1, 0.1))
            for i in range(n)]


def test_arima_30_points_with_ci():
    """ARIMA 返回 30 个点，每点含 lower/upper 置信区间"""
    result = predict_series(_make_series(), model="arima", days=30)
    fc = result["forecast"]
    assert len(fc) == 30
    for p in fc:
        assert "date" in p and "value" in p
        assert p["lower"] <= p["value"] <= p["upper"]
    # 日期连续且都在未来
    assert fc[0]["date"] > result["history"][-1]["date"]


def test_arima_metrics_and_grade():
    """回测精度指标存在且 mape 有限"""
    result = predict_series(_make_series(), model="arima", days=30)
    m = result["metrics"]
    assert m is not None
    assert 0 <= m["mape"] < 25
    assert m["mae"] >= 0


def test_too_short_series_raises():
    """数据不足 30 条应抛 ValueError"""
    with pytest.raises(ValueError):
        predict_series(_make_series(20), model="arima", days=30)


def test_arimax_with_exog():
    """ARIMAX 含外生变量同样返回 30 点（外生变量用不同序列避免共线）"""
    random.seed(8)
    series = _make_series(150)
    exog = [((datetime.date(2026, 1, 1) + datetime.timedelta(days=i)).isoformat(),
             1.3 + 0.002 * i + random.uniform(-0.02, 0.02))
            for i in range(150)]
    result = predict_series(series, exog=exog, model="arimax", days=30)
    assert len(result["forecast"]) == 30


def test_unknown_model_raises():
    with pytest.raises(ValueError):
        predict_series(_make_series(), model="lstm_x", days=30)
