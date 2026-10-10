# -*- coding: utf-8 -*-
"""
周报生成：docs/reports/weekly_YYYY-MM-DD.md

内容：本周（或指定周）定西核心四项价格、环比/同比、数据源、异常提示、下周 ARIMAX 预测。
用法：
  cd backend
  set DB_PASSWORD=***
  venv\\Scripts\\python.exe scripts\\gen_weekly_report.py            # 本周
  venv\\Scripts\\python.exe scripts\\gen_weekly_report.py 2026-W40   # 指定周
数据不足时优雅跳过并提示。
"""
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import SessionLocal                                # noqa: E402
from service.price_service import get_trend, get_yoy          # noqa: E402

REGION_ID = 12            # 定西（当前唯一周报源）
CORE = [(1, "活牛"), (3, "活羊"), (5, "玉米"), (6, "豆粕")]
SRC_CN = {"gov": "政府监测", "derived": "反推补全", "index": "红牛指数", "manual": "示例数据"}


def week_range(iso_week=None):
    """返回 (周一, 周日, 标签)。默认本周。"""
    today = date.today()
    if iso_week:
        year, week = int(iso_week.split("-W")[0]), int(iso_week.split("-W")[1])
        monday = date.fromisocalendar(year, week, 1)
    else:
        monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6), "%d-W%02d" % (
        monday.isocalendar()[0], monday.isocalendar()[1])


def main(iso_week=None):
    monday, sunday, label = week_range(iso_week)
    db = SessionLocal()
    lines = ["# 价格周报（%s：%s ~ %s）" % (label, monday, sunday), ""]

    try:
        # 本周价格（取该周内每个分类的最近点；周报数据按发布日落周）
        trend = get_trend(db, category_id=CORE[0][0], region_id=REGION_ID,
                          start_date=str(monday), end_date=str(sunday))
        if not trend["points"]:
            # 无本周数据时回退到最近可得点并注明
            latest = get_trend(db, category_id=CORE[0][0], region_id=REGION_ID,
                               start_date=str(monday - timedelta(days=120)))
            if not latest["points"]:
                print("该周数据不足：分类%d在 %s ~ %s 无数据，且近120天无可回退数据" %
                      (CORE[0][0], monday, sunday))
                return None
            lines.append("> 注：%s 周内暂无数据，以下为最近可得数据。" % label)
        db.close()

        # 每个核心分类：本周最近点 + 环比同比 + 来源
        rows = []
        for cid, cname in CORE:
            db2 = SessionLocal()
            try:
                t = get_trend(db2, category_id=cid, region_id=REGION_ID,
                              start_date=str(monday - timedelta(days=240)))
                pts = t["points"]
                if not pts:
                    rows.append((cname, None, None, None, None, None))
                    continue
                last = pts[-1]
                # 环比：与上一个数据点比（周更口径）
                prev = pts[-2]["price"] if len(pts) >= 2 else None
                mom = round((last["price"] - prev) / prev * 100, 1) if prev else None
                # 同比：与一年内同点比（简化：与240天前第一个点比较标注近似）
                yoy = None
                try:
                    y = get_yoy(db2, cid, REGION_ID,
                                ref_date=last["date"])
                    yoy = y.get("yoy_pct")
                except Exception:
                    pass
                rows.append((cname, last["price"], last["date"], mom, yoy,
                             SRC_CN.get(last.get("source") or "", last.get("source"))))
            finally:
                db2.close()

        lines += ["## 核心价格（%s）" % ("定西周报" if rows and rows[0][5] else ""),
                  "",
                  "| 分类 | 最近价(元/斤) | 数据日期 | 环比% | 同比% | 来源 |",
                  "|------|--------------|---------|-------|-------|------|"]
        missing = []
        for cname, price, d, mom, yoy, src in rows:
            if price is None:
                missing.append(cname)
                lines.append("| %s | — | — | — | — | 该周数据不足 |" % cname)
            else:
                fmt = lambda v: ("—" if v is None else ("%+.1f" % v))
                lines.append("| %s | %.2f | %s | %s | %s | %s |" %
                             (cname, price, d, fmt(mom), fmt(yoy), src))
        lines.append("")

        # 异常提示
        abnormal = [r for r in rows if r[3] is not None and abs(r[3]) >= 5]
        if abnormal:
            lines.append("## ⚠ 异常提示")
            lines += ["- %s 环比波动 %.1f%%（≥5%%）" % (r[0], r[3]) for r in abnormal]
            lines.append("")
        if missing:
            lines.append("> 数据缺失：%s（源站该周未发布）" % "、".join(missing))
            lines.append("")

        # 下周预测（活牛 ARIMAX，数据不足时跳过）
        lines.append("## 下周预测（活牛 ARIMAX，仅供参考）")
        dbp = SessionLocal()
        try:
            from service.predict_service import run_predict
            pred = run_predict(dbp, category_id=1,
                               region_id=REGION_ID, days=7, model="arimax")
            fc = pred.get("forecast", [])
            if fc:
                lo = min(p["value"] for p in fc)
                hi = max(p["value"] for p in fc)
                m = pred.get("metrics", {})
                lines.append("- 未来7天区间：%.2f ~ %.2f 元/斤（MAPE %.2f%%，%s）" %
                             (lo, hi, m.get("mape", "-"), m.get("grade", "-")))
            else:
                lines.append("- 历史数据不足，无法预测")
        except Exception as e:
            lines.append("- 预测不可用：%s" % str(e)[:60])
        finally:
            dbp.close()
        lines.append("")

        lines.append("---")
        lines.append("*生成时间：%s　数据源：定西市畜牧兽医局周报（gov）+ 反推补全（derived），"
                     "默认不含示例数据。*" % datetime.now().strftime("%Y-%m-%d %H:%M"))

        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "docs", "reports")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "weekly_%s.md" % str(monday))
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("周报已生成:", out)
        return out
    finally:
        pass


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
