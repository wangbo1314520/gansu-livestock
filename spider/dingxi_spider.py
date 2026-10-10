# -*- coding: utf-8 -*-
"""
定西市畜牧兽医局价格爬虫（已实测可用 2026-10-10）

数据形态：
  - 栏目"草牧产业>市场动态"（columnid=8319），大汉版通 CMS
  - 列表经 /module/web/jpage/dataproxy.jsp 接口返回（XML，含标题/链接/日期）
  - 周报《N月第N周畜产品和饲料集贸市场价格情况》为农业农村部体系转载（正文段落，
    含"主产省份活牛价格30.49元/公斤"等句式）
  - 季报《定西市第N季度…》为本地口径（"活牛全市均价30.30元/公斤"句式）

解析策略：按品类多模式正则（部级转载优先"主产省份/全国"，季报用"全市均价"），
单位 元/公斤 ÷ 2 -> 元/斤；record_date 用页面发布时间。
请求间隔 >= 3 秒，UA = gansu-livestock-research/1.0。
"""
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# 直接执行本文件时把项目根加入 sys.path 以导入 spider 包
_PROJECT_ROOT = re.search(r"^(.*gansu-livestock)", __file__).group(1)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from spider.gov_spider import BaseSpider

BASE = "http://xmj.dingxi.gov.cn"
DATAPROXY = BASE + "/module/web/jpage/dataproxy.jsp"
COLUMN_ID = 8319
UNIT_ID = 21724

# 品类 -> 正则模式列表（依次尝试，元/公斤）
CATEGORY_PATTERNS = {
    "活牛": [r"主产省份活牛价格(\d+\.?\d*)元/公斤", r"活牛全市均价(\d+\.?\d*)元/公斤"],
    "牛肉": [r"全国牛肉平均价格(\d+\.?\d*)元/公斤", r"牛肉全市均价(\d+\.?\d*)元/公斤"],
    "活羊": [r"主产省份活羊价格(\d+\.?\d*)元/公斤", r"活羊全市均价(\d+\.?\d*)元/公斤"],
    "羊肉": [r"全国羊肉平均价格(\d+\.?\d*)元/公斤", r"羊肉全市均价(\d+\.?\d*)元/公斤"],
    "玉米": [r"全国玉米平均价格(\d+\.?\d*)元/公斤", r"玉米全市均价(\d+\.?\d*)元/公斤"],
    "豆粕": [r"全国豆粕平均价格(\d+\.?\d*)元/公斤", r"豆粕全市均价(\d+\.?\d*)元/公斤"],
}


class DingxiSpider(BaseSpider):
    """定西市畜牧兽医局周报/季报爬虫"""

    def list_reports(self, max_items=30):
        """dataproxy 接口拿文章列表，筛"价格"周报（也含季报）"""
        params = {"page": 1, "appid": 1, "webid": 72, "path": "/",
                  "columnid": COLUMN_ID, "unitid": UNIT_ID, "webname": "%E5%AE%9A%E8%A5%BF"}
        resp = self.get(DATAPROXY, params=params)
        total = int(re.search(r"<totalrecord>(\d+)</totalrecord>", resp.text).group(1))
        self.log("栏目共 %d 条记录" % total)

        reports = []
        # 每条 record: <a href="/art/...html" ...><div ... title="标题">标题</div>...[日期]
        for m in re.finditer(
                r'href="(/art/[^"]+)"[^>]*>.*?title="([^"]*)".*?\[(\d{4}-\d{2}-\d{2})\]',
                resp.text, re.S):
            url, title, date = m.group(1), m.group(2), m.group(3)
            if "价格" not in title:
                continue
            reports.append((title, BASE + url, date))
            if len(reports) >= max_items:
                break
        self.log("筛出价格类报告 %d 篇" % len(reports))
        return reports

    @staticmethod
    def _normalize(text):
        """全角转半角（正文偶混用 ／．％ 等）"""
        out = []
        for ch in text:
            code = ord(ch)
            if code == 0xFF0F:
                out.append("/")
            elif code == 0xFF0E:
                out.append(".")
            elif 0xFF01 <= code <= 0xFF5E:
                out.append(chr(code - 0xFEE0))
            else:
                out.append(ch)
        return "".join(out)

    def parse_report(self, url):
        """解析一篇报告 -> {品类: 元/公斤} + 日期"""
        resp = self.get(url)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        text = self._normalize(soup.body.get_text("\n", strip=True))

        date_m = re.search(r"发布时间[:：]\s*(\d{4}-\d{2}-\d{2})", text)
        report_date = date_m.group(1) if date_m else str(datetime.now().date())

        prices = {}
        for category, patterns in CATEGORY_PATTERNS.items():
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    prices[category] = float(m.group(1))
                    break
            else:
                self.log("  [WARN] %s 未匹配（该期可能无此项）: %s" % (category, url))
        return prices, report_date

    def run(self, max_reports=5):
        """抓取 -> 解析 -> 标准记录（元/斤）"""
        reports = self.list_reports(max_items=max_reports * 4)[:max_reports]
        records = []
        for title, url, list_date in reports:
            try:
                prices, report_date = self.parse_report(url)
                if not prices:
                    self.log("  [SKIP] 无可提取价格: %s" % title[:30])
                    continue
                for category, price_kg in prices.items():
                    records.append({
                        "region": "定西市",
                        "category": category,
                        "price": round(price_kg / 2, 2),   # 元/公斤 -> 元/斤
                        "unit": "元/斤",
                        "date": report_date,
                        "source": "gov",
                        "source_detail": "定西市畜牧兽医局",
                        "report_title": title,
                    })
                self.log("  %s -> %d 项" % (title[:34], len(prices)))
            except Exception as e:
                self.log("  [FAIL] %s: %s" % (title[:30], e))
        self.log("共提取 %d 条记录" % len(records))
        return records


if __name__ == "__main__":
    spider = DingxiSpider()
    data = spider.run(max_reports=5)
    import json
    import os
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "dingxi_test.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("试抓结果已保存:", out)
