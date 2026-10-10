# -*- coding: utf-8 -*-
"""
数据预处理（需求文档 8.1）：
  1. 按日期排序、缺失日期插值
  2. 异常值检测（IQR 替换为 NaN 再插值）
  3. 平稳性检验（ADF）
  4. 差分（如需）
"""
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def to_series(data):
    """
    [(date_str, value), ...] -> pd.Series（DatetimeIndex，升序，日频）
    同日多条自动取均值
    """
    if isinstance(data, pd.Series):
        return data.sort_index()
    df = pd.DataFrame(data, columns=["date", "price"])
    df["date"] = pd.to_datetime(df["date"])
    s = df.groupby("date")["price"].mean().sort_index()
    return s


def fill_missing(s: pd.Series) -> pd.Series:
    """重采样为日频，缺失日线性插值（政府周报数据中间会有空洞）"""
    s = s.resample("D").mean()
    return s.interpolate(method="linear").bfill().ffill()


def replace_outliers(s: pd.Series) -> pd.Series:
    """IQR 异常值替换为 NaN 后插值（不直接删除，保持日期连续）"""
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return s
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    cleaned = s.where((s >= lo) & (s <= hi))
    return cleaned.interpolate(method="linear").bfill().ffill()


def adf_test(s: pd.Series, alpha=0.05):
    """
    ADF 平稳性检验
    返回 {"statistic", "pvalue", "is_stationary"}
    """
    result = adfuller(s.dropna(), autolag="AIC", result_object=False)
    return {
        "statistic": round(float(result[0]), 4),
        "pvalue": round(float(result[1]), 4),
        "is_stationary": result[1] < alpha,
    }


def suggest_d(s: pd.Series, max_d: int = 2) -> int:
    """根据 ADF 检验建议差分阶数 d"""
    d = 0
    current = s.copy()
    while d < max_d:
        if adf_test(current)["is_stationary"]:
            break
        current = current.diff().dropna()
        d += 1
    return d


def prepare(data):
    """完整预处理流水线：排序 -> 插值 -> 去异常 -> 平稳性信息"""
    s = to_series(data)
    s = fill_missing(s)
    s = replace_outliers(s)
    adf = adf_test(s)
    d = suggest_d(s)
    return {
        "series": s,
        "adf": adf,
        "d": d,
        "n_points": len(s),
    }
