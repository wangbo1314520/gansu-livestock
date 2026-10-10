# -*- coding: utf-8 -*-
"""
生成示例价格数据 SQL（gansu_livestock.price_data）

数据特征（模拟甘肃 2023-2026 真实行情）：
  - 长期趋势：牛羊价 2023-2024 缓慢下行，2025 触底，2026 回升
  - 季节性：春节前后走高，夏季偏低
  - 饲料价：玉米/豆粕随农产品周期波动，麸皮跟随玉米
  - 随机扰动：±3% 白噪声；地区差异：各市州固定 ±5% 偏移

生成范围：
  - 省级（region_id=1）：8 个分类全部，周频（2023-01-01 ~ 2026-10-10）
  - 6 个市州（张掖/武威/平凉/庆阳/临夏/甘南）：4 个牲畜分类，双周频
  - 记录数约 3960 条（目标 3000-6000）

用法：
  E:\\Program\\gansu-livestock\\backend\\venv\\Scripts\\python.exe gen_sample_data.py
输出：
  E:\\Program\\gansu-livestock\\backend\\sql\\sample_data.sql
"""
import math
import random
from datetime import date, timedelta

random.seed(42)   # 固定种子，可重现

OUT_PATH = r"E:\Program\gansu-livestock\backend\sql\sample_data.sql"

# ------------------------------------------------------------------
# 基础维度（id 已从数据库查询确认，与 init_data.sql 一致）
# ------------------------------------------------------------------
PROVINCE_ID = 1
CITY_REGIONS = [
    (8, "张掖市"), (7, "武威市"), (9, "平凉市"),
    (11, "庆阳市"), (14, "临夏州"), (15, "甘南州"),
]

# (category_id, 名称, 2023年初基准价 元/斤, 类型)
CATEGORIES = [
    (1, "活牛", 17.0, "livestock"),
    (2, "牛肉", 38.0, "livestock"),
    (3, "活羊", 15.0, "livestock"),
    (4, "羊肉", 35.0, "livestock"),
    (5, "玉米", 1.3, "feed"),
    (6, "豆粕", 2.2, "feed"),
    (7, "麸皮", 0.9, "feed"),
    (8, "苜蓿草", 1.4, "feed"),
]

START = date(2023, 1, 1)
END = date(2026, 10, 10)

# ------------------------------------------------------------------
# 价格模型
# ------------------------------------------------------------------
# 牛羊长期趋势（分段线性，年化变化率）：
#   2023初1.00 → 2024初0.92（约-8%）→ 2025初0.85（-7.6%）
#   → 2026初0.82（触底-3.5%）→ 2026.77约0.87（回升+8%/年）
LIVESTOCK_TREND = [
    (2023.00, 1.00), (2024.00, 0.92),
    (2025.00, 0.85), (2026.00, 0.82), (2026.80, 0.87),
]

# 饲料长期趋势：玉米/麸皮缓慢下行（产能提升），豆粕/苜蓿草走平
FEED_TREND = {
    "玉米": [(2023.0, 1.00), (2026.8, 0.93)],
    "麸皮": [(2023.0, 1.00), (2026.8, 0.94)],
    "豆粕": [(2023.0, 1.00), (2026.8, 1.00)],
    "苜蓿草": [(2023.0, 1.00), (2026.8, 1.02)],
}

# 季节性系数（月）：春节前后走高，夏季偏低（牛羊与饲料共用形状，幅度不同）
SEASON_LIVESTOCK = {1: 1.05, 2: 1.06, 3: 1.02, 4: 1.00, 5: 1.00,
                    6: 0.96, 7: 0.96, 8: 0.96, 9: 1.01, 10: 1.01, 11: 1.02, 12: 1.04}
SEASON_FEED = {1: 1.02, 2: 1.03, 3: 1.00, 4: 0.99, 5: 0.99,
               6: 0.98, 7: 0.98, 8: 0.99, 9: 1.00, 10: 1.00, 11: 1.01, 12: 1.02}


def year_frac(d: date) -> float:
    """日期 -> 小数年（2023-07-02 ≈ 2023.5）"""
    return d.year + (d.timetuple().tm_yday - 1) / 365.0


def piecewise(points, x):
    """分段线性插值"""
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return points[-1][1]


def livestock_price(name, base, d: date) -> float:
    """牛羊价：趋势 × 季节 × ±3% 噪声"""
    t = year_frac(d)
    trend = piecewise(LIVESTOCK_TREND, t)
    season = SEASON_LIVESTOCK[d.month]
    noise = 1.0 + random.uniform(-0.03, 0.03)
    return base * trend * season * noise


def feed_price(name, base, d: date) -> float:
    """饲料价：趋势 × 周期波动 × 轻季节 × ±3% 噪声
    玉米/麸皮同相位（周期约 1.5 年），豆粕周期更短、幅度更大，苜蓿草平缓
    """
    t = year_frac(d)
    trend = piecewise(FEED_TREND[name], t)
    if name in ("玉米", "麸皮"):
        cycle = 1.0 + 0.06 * math.sin(2 * math.pi * (t - 2023.2) / 1.5)
    elif name == "豆粕":
        cycle = 1.0 + 0.10 * math.sin(2 * math.pi * (t - 2023.5) / 1.0)
    else:  # 苜蓿草
        cycle = 1.0 + 0.04 * math.sin(2 * math.pi * (t - 2023.0) / 2.0)
    season = SEASON_FEED[d.month]
    noise = 1.0 + random.uniform(-0.03, 0.03)
    return base * trend * cycle * season * noise


def gen_price(cat_id, name, base, kind, d: date, region_offset: float) -> float:
    """生成一条价格：主模型 × 地区固定偏移，保留 2 位小数"""
    if kind == "livestock":
        p = livestock_price(name, base, d)
    else:
        p = feed_price(name, base, d)
    return round(max(p * region_offset, 0.1), 2)


def week_fridays(step_days=7):
    """从 START 到 END 按 step_days 步进生成日期序列"""
    d = START
    while d <= END:
        yield d
        d += timedelta(days=step_days)


def make_rows():
    """生成全部 (region_id, category_id, price, date) 行"""
    rows = []
    # 省级：8 分类 × 周频
    for cat_id, name, base, kind in CATEGORIES:
        for d in week_fridays(7):
            rows.append((PROVINCE_ID, cat_id,
                         gen_price(cat_id, name, base, kind, d, 1.0), d))
    # 市州：4 牲畜分类 × 双周频 × 固定地区偏移(±5%)
    for region_id, region_name in CITY_REGIONS:
        for cat_id, name, base, kind in CATEGORIES:
            if kind != "livestock":
                continue
            offset = random.uniform(0.95, 1.05)   # 每个(地区,分类)固定偏移
            for d in week_fridays(14):
                rows.append((region_id, cat_id,
                             gen_price(cat_id, name, base, kind, d, offset), d))
    return rows


def write_sql(rows):
    """写 INSERT IGNORE 批量语句（每 500 行一条 INSERT）"""
    lines = [
        "-- 示例价格数据（脚本生成，种子 42，可重现）",
        "-- 范围: %s ~ %s，共 %d 条" % (START, END, len(rows)),
        "USE gansu_livestock;",
        "SET NAMES utf8mb4;",
        "",
    ]
    cols = "(region_id, category_id, price, unit, source, source_detail, record_date)"
    for i in range(0, len(rows), 500):
        chunk = rows[i:i + 500]
        values = ",\n".join(
            "(%d, %d, %.2f, '元/斤', 'manual', '示例数据', '%s')"
            % (rid, cid, price, d.isoformat())
            for rid, cid, price, d in chunk
        )
        lines.append("INSERT IGNORE INTO price_data %s VALUES\n%s;" % (cols, values))
        lines.append("")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    rows = make_rows()
    write_sql(rows)
    insert_count = sum(1 for line in open(OUT_PATH, encoding="utf-8")
                       if line.startswith("INSERT IGNORE"))
    print("生成完成: %s" % OUT_PATH)
    print("记录数: %d（省级周频 + 6市州双周频）" % len(rows))
    print("INSERT 语句: %d 条（每条500行）" % insert_count)
    # 抽样打印便于人工核对量级
    from collections import defaultdict
    sample = defaultdict(list)
    for rid, cid, price, d in rows:
        if rid == 1:
            sample[cid].append((d, price))
    for cat_id, name, base, _ in CATEGORIES:
        series = sorted(sample[cat_id])
        head, tail = series[0], series[-1]
        print("  %-4s 基准%.1f | %s=%.2f -> 2025年中=%.2f -> %s=%.2f"
              % (name, base, head[0], head[1],
                 dict(series).get(date(2025, 6, 30), 0) or series[len(series)//2][1],
                 tail[0], tail[1]))
