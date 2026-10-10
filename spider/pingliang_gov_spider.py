# -*- coding: utf-8 -*-
"""
平凉市畜牧兽医局价格爬虫（2026-10-10 实测可用）

数据形态：
  - 站点 http://xmsy.pingliang.gov.cn/（新版政府站群，hash 文件名，无 dataproxy 接口）
  - 首页滚动窗口发布最近 6 期《N月第N周畜产品和饲料集贸市场价格情况》
    （栏目 /scxq/ 列表页为 JS 渲染，首页链接是唯一静态入口）
  - 正文与定西周报同体系（农业农村部转载："主产省份活牛价格X元/公斤"等句式），
    解析复用 dingxi_spider.CATEGORY_PATTERNS

入库注意：该周报为全国/主产省份口径（非平凉本地价），与定西周报同源同数值，
region 标平凉市仅表示"经平凉畜牧局发布渠道可得的参考序列"。
请求间隔 >= 3 秒，UA = gansu-livestock-research/1.0。
"""
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

_PROJECT_ROOT = re.search(r"^(.*gansu-livestock)", __file__).group(1)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from spider.gov_spider import BaseSpider
from spider.dingxi_spider import CATEGORY_PATTERNS, DingxiSpider

BASE = "http://xmsy.pingliang.gov.cn"
UA = "gansu-livestock-research/1.0"


class PingliangGovSpider(BaseSpider):
    """平凉市畜牧兽医局周报爬虫（首页窗口模式）"""

    NAME = "pingliang_gov"

    def __init__(self):
        super().__init__()
        self.session.headers["User-Agent"] = UA

    def _get(self, url, **kwargs):
        time.sleep(3)
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp

    def list_reports(self):
        """首页滚动窗口的价格类文章 [{url, title}]（无静态列表页/接口）"""
        resp = self._get(BASE + "/")
        resp.encoding = "utf-8"
        links = re.findall(
            r'href="(/scxq/art/[^"]+\.html)"[^>]*>([^<]*价格[^<]*)<', resp.text)
        seen, reports = set(), []
        for url, title in links:
            if url in seen:
                continue
            seen.add(url)
            reports.append({"url": BASE + url, "title": title.strip()})
        self.log("首页窗口筛出价格类报告 %d 篇" % len(reports))
        return reports

    def parse_report(self, url):
        """解析一篇报告 -> {品类: 元/公斤} + 发布日期"""
        resp = self._get(url)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        text = DingxiSpider._normalize(soup.body.get_text("\n", strip=True))

        # 日期：新版站群用 meta MakeTime/PublishDate，正文无"发布时间"字样
        report_date = None
        meta = soup.find("meta", attrs={"name": "MakeTime"}) or \
            soup.find("meta", attrs={"name": "PublishDate"})
        if meta and meta.get("content"):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", meta["content"])
            if m:
                report_date = m.group(1)

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

    def run(self, max_reports=6):
        """抓首页窗口 -> 解析 -> 标准记录（元/斤）"""
        records = []
        for item in self.list_reports()[:max_reports]:
            try:
                prices, report_date = self.parse_report(item["url"])
                if not prices:
                    self.log("  [SKIP] 无可提取价格: %s" % item["title"][:30])
                    continue
                if not report_date:
                    self.log("  [SKIP] 无发布日期: %s" % item["title"][:30])
                    continue
                for category, price_kg in prices.items():
                    records.append({
                        "region": "平凉市",
                        "category": category,
                        "price": round(price_kg / 2, 2),   # 元/公斤 -> 元/斤
                        "unit": "元/斤",
                        "date": report_date,
                        "source": "gov",
                        "source_detail": "平凉市畜牧兽医局",
                        "report_title": item["title"],
                    })
                self.log("  %s -> %d 项" % (item["title"][:34], len(prices)))
            except Exception as e:
                self.log("  [FAIL] %s: %s" % (item["title"][:30], e))
        self.log("共提取 %d 条记录" % len(records))
        return records


if __name__ == "__main__":
    import json
    for rec in PingliangGovSpider().run():
        print(json.dumps(rec, ensure_ascii=False))
