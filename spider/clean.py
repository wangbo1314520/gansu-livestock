# -*- coding: utf-8 -*-
"""
数据清洗：把爬虫原始 JSON 清洗成可入库的标准 DataFrame
规则（需求文档 8.1）：
  1. 品类/地区名归一化（映射到标准 8 分类、15 地区）
  2. 价格转 float，单位统一元/斤（元/kg -> /2）
  3. 异常值检测（IQR），标记不删除
  4. 去重（同地区+分类+日期+来源）
用法：
  python clean.py data/raw/gov_20261010.json -> data/clean/gov_20261010_clean.json
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 标准分类与别名映射（爬到的名字 -> 标准名）
CATEGORY_ALIAS = {
    "活牛": "活牛", "牛": "活牛", "育肥牛": "活牛", "架子牛": "活牛", "犊牛": "活牛",
    "牛肉": "牛肉", "去骨牛肉": "牛肉", "鲜牛肉": "牛肉", "牛腩": "牛肉",
    "活羊": "活羊", "羊": "活羊", "育肥羊": "活羊", "羔羊": "活羊",
    "羊肉": "羊肉", "带骨羊肉": "羊肉", "鲜羊肉": "羊肉",
    "玉米": "玉米", "玉米粒": "玉米", "干玉米": "玉米",
    "豆粕": "豆粕", "豆饼": "豆粕",
    "麸皮": "麸皮", "小麦麸": "麸皮",
    "苜蓿": "苜蓿草", "苜蓿草": "苜蓿草", "紫花苜蓿": "苜蓿草", "草捆": "苜蓿草",
}

# 地区别名（爬到的写法 -> 标准市州名）
REGION_ALIAS = {
    "兰州": "兰州市", "嘉峪关": "嘉峪关市", "金昌": "金昌市", "白银": "白银市",
    "天水": "天水市", "武威": "武威市", "张掖": "张掖市", "平凉": "平凉市",
    "酒泉": "酒泉市", "庆阳": "庆阳市", "定西": "定西市", "陇南": "陇南市",
    "临夏": "临夏州", "甘南": "甘南州",
    "甘肃": "甘肃省", "甘肃省": "甘肃省", "全省": "甘肃省",
}


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """字段归一化：分类、地区、单位、日期"""
    df = df.copy()

    # 分类归一化
    df["category"] = df["category"].map(lambda x: CATEGORY_ALIAS.get(str(x).strip(), None))
    df = df[df["category"].notna()]

    # 地区归一化（默认全省）
    df["region"] = df["region"].map(
        lambda x: REGION_ALIAS.get(str(x).strip(), "甘肃省"))

    # 价格转 float；单位统一元/斤
    df["price"] = df["price"].map(_to_price)
    unit_is_kg = df["unit"].astype(str).str.contains("kg|千克", case=False)
    df.loc[unit_is_kg, "price"] = df.loc[unit_is_kg, "price"] / 2   # 元/kg -> 元/斤
    df = df[df["price"].notna()]
    df["unit"] = "元/斤"

    # 日期解析；解析失败用抓取当天
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["date"] = df["date"].fillna(pd.Timestamp.now().strftime("%Y-%m-%d"))

    return df


def _to_price(v):
    """'12.5元' / '12.5' / 12.5 -> float，失败 None"""
    if pd.isna(v):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", str(v))
    return float(m.group(1)) if m else None


def mark_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """IQR 异常值标记：同 category 分组，超出 [Q1-1.5IQR, Q3+1.5IQR] 标记 is_outlier"""
    df = df.copy()
    df["is_outlier"] = False
    for cat, group in df.groupby("category"):
        q1, q3 = group["price"].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        if iqr == 0:                      # 无波动不判异常
            continue
        df.loc[group.index, "is_outlier"] = (group["price"] < lo) | (group["price"] > hi)
    return df


def dedup(df: pd.DataFrame) -> pd.DataFrame:
    """去重：地区+分类+日期+来源 相同只留一条"""
    return df.drop_duplicates(subset=["region", "category", "date", "source"],
                              keep="last")


def clean_file(input_path: str, output_path: str = None):
    """清洗一个原始 JSON 文件"""
    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not raw:
        print("原始文件为空，跳过")
        return None

    df = pd.DataFrame(raw)
    df = normalize(df)
    df = dedup(df)
    df = mark_outliers(df)

    if output_path is None:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(PROJECT_ROOT, "data", "clean", base + "_clean.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_json(output_path, orient="records", force_ascii=False, indent=2)

    print("清洗完成: %d 条 -> %s" % (len(df), output_path))
    print("  分类分布:", df["category"].value_counts().to_dict())
    print("  异常值:", int(df["is_outlier"].sum()), "条")
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python clean.py <原始JSON路径> [输出路径]")
        sys.exit(1)
    clean_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
