# -*- coding: utf-8 -*-
"""
月报生成：docs/reports/monthly_YYYY-MM.md（含 matplotlib 月度走势图 png）

内容：上月定西核心四项月度均价、环比/同比、数据源、月度走势图。
用法：
  cd backend
  set DB_PASSWORD=***
  venv\\Scripts\\python.exe scripts\\gen_monthly_report.py            # 上月
  venv\\Scripts\\python.exe scripts\\gen_monthly_report.py 2026-09   # 指定月
数据不足时优雅提示退出。
"""
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt           # noqa: E402

from model import SessionLocal            # noqa: E402
from service.price_service import get_trend  # noqa: E402

REGION_ID = 12
CORE = [(1, "活牛"), (3, "活羊"), (5, "玉米"), (6, "豆粕")]
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]   # 中文
plt.rcParams["axes.unicode_minus"] = False


def month_span(ym=None):
    """返回 (年, 月, 起日, 止日)。默认上月。"""
    if ym:
        y, m = int(ym.split("-")[0]), int(ym.split("-")[1])
    else:
        today = date.today()
        y, m = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    start = date(y, m, 1)
    end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return y, m, start, end - __import__("datetime").timedelta(days=1)


def main(ym=None):
    y, m, start, end = month_span(ym)
    db = SessionLocal()
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "docs", "reports")
    os.makedirs(report_dir, exist_ok=True)

    stats, any_data = [], False
    for cid, cname in CORE:
        t = get_trend(db, category_id=cid, region_id=REGION_ID,
                      start_date=str(start - __import__("datetime").timedelta(days=400)),
                      end_date=str(end))
        pts = [p for p in t["points"]]
        cur = [p for p in pts if start.isoformat() <= p["date"] <= end.isoformat()]
        if not cur:
            stats.append((cname, None, None, None, None))
            continue
        any_data = True
        avg = round(sum(p["price"] for p in cur) / len(cur), 2)
        # 环比：与上一个数据点比；同比：与 350~380 天前最近点比（简化）
        prev_pt = next((p for p in reversed(pts) if p["date"] < start.isoformat()), None)
        mom = round((cur[-1]["price"] - prev_pt["price"]) / prev_pt["price"] * 100, 1) \
            if prev_pt else None
        year_ago = [p for p in pts if "YEARAGO" == "YEARAGO" and
                    abs((datetime.strptime(p["date"], "%Y-%m-%d") -
                         datetime.strptime(cur[-1]["date"], "%Y-%m-%d")).days - 365) <= 30]
        yoy = round((cur[-1]["price"] - year_ago[-1]["price"]) / year_ago[-1]["price"] * 100, 1) \
            if year_ago else None
        stats.append((cname, avg, len(cur), mom, yoy))

    if not any_data:
        print("该月数据不足：%d-%02d 无任何核心分类数据" % (y, m))
        return None

    # 月度走势图（12 个月窗口）
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (cid, cname) in zip(axes.flat, CORE):
        t = get_trend(db, category_id=cid, region_id=REGION_ID,
                      start_date=str(date(y, m, 1) - __import__("datetime").timedelta(days=365)))
        dates = [p["date"] for p in t["points"]]
        vals = [p["price"] for p in t["points"]]
        ax.plot(dates, vals, marker="o", markersize=3, linewidth=1.2, color="#409eff")
        ax.set_title(cname, fontsize=11)
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("定西核心价格月度走势（%d-%02d 及近一年）" % (y, m), fontsize=13)
    fig.tight_layout()
    fig_path = os.path.join(report_dir, "figure_monthly_%d-%02d.png" % (y, m))
    fig.savefig(fig_path, dpi=110)
    plt.close(fig)
    db.close()

    lines = ["# 价格月报（%d-%02d）" % (y, m), "",
             "| 分类 | 月均(元/斤) | 数据点数 | 环比% | 同比% |",
             "|------|------------|---------|-------|-------|"]
    for cname, avg, n, mom, yoy in stats:
        if avg is None:
            lines.append("| %s | — | 0 | — | — |" % cname)
        else:
            fmt = lambda v: "—" if v is None else "%+.1f" % v
            lines.append("| %s | %.2f | %d | %s | %s |" % (cname, avg, n, fmt(mom), fmt(yoy)))
    lines += ["", "![月度走势](figure_monthly_%d-%02d.png)" % (y, m), "",
              "*数据源：定西市畜牧兽医局周报（gov）+ 反推补全（derived），默认不含示例数据。*",
              "*生成时间：%s*" % datetime.now().strftime("%Y-%m-%d %H:%M")]

    out = os.path.join(report_dir, "monthly_%d-%02d.md" % (y, m))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("月报已生成:", out, "| 图:", fig_path)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
