# -*- coding: utf-8 -*-
"""
统一预测入口（供 backend/service/predict_service.py 调用）

predict_series(series, exog=None, model="arima", days=30)
  series: [(date_str, value), ...]     主序列（牛羊价格）
  exog:   [(date_str, value), ...]     外生序列（饲料价格，arimax 用）
  model:  "arima" | "arimax"
返回：
  {
    "history":  [{date, value}, ...],                 # 最近90天历史
    "forecast": [{date, value, lower, upper}, ...],   # 未来 days 天
    "metrics":  {mae, rmse, mape, grade} or None,     # 回测精度
    "order":    使用的模型阶数
  }
"""
from predict import arima_model, arimax_model
from predict.evaluate import backtest, grade
from predict.preprocess import prepare


def predict_series(series, exog=None, model="arima", days=30):
    """统一入口：预处理 -> 拟合预测 -> 回测评价"""
    prep = prepare(series)
    s = prep["series"]
    if len(s) < 30:
        raise ValueError("预处理后有效数据 %d 条，不足30条，无法建模" % len(s))

    if model == "arimax":
        if exog is None:
            raise ValueError("arimax 需要 exog（饲料价格序列）")
        exog_prep = prepare(exog)
        fc, order = arimax_model.fit_forecast(s, exog_prep["series"], days=days)

        def _bt(train):
            out, _ = arimax_model.fit_forecast(train, exog_prep["series"].reindex(
                train.index).ffill().bfill(), days=days)
            return out["mean"].values
    elif model == "arima":
        fc, order = arima_model.fit_forecast(s, days=days)

        def _bt(train):
            out, _ = arima_model.fit_forecast(train, days=days)
            return out["mean"].values
    else:
        raise ValueError("未知模型: %s（支持 arima / arimax）" % model)

    # 回测精度（数据足够才算）
    metrics = backtest(_bt, s, test_days=min(30, len(s) // 3))
    if metrics:
        metrics["grade"] = grade(metrics.get("mape", float("nan")))

    return {
        "history": [{"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
                    for d, v in s.tail(90).items()],
        "forecast": [{"date": d.strftime("%Y-%m-%d"),
                      "value": round(float(r["mean"]), 2),
                      "lower": round(float(r["lower"]), 2),
                      "upper": round(float(r["upper"]), 2)}
                     for d, r in fc.iterrows()],
        "metrics": metrics,
        "order": list(order) if order else None,
        "adf": prep["adf"],
    }
