# -*- coding: utf-8 -*-
"""平凉红牛价格指数爬虫

数据源：新华·中国平凉红牛价格指数月报（中国经济信息社 × 平凉市人民政府发布）
定位方式：东方财富搜索接口（search-api-web.eastmoney.com）检索"平凉红牛价格指数"，
          筛选标题含"月报"的文章，正文含活牛/S级胴体/牛脑髓三类价格与指数点位。
产出：region=平凉市, category=活牛, unit=元/斤, source=index
      remark 记录指数点位与 S 级胴体价。
"""
import json
import re
import sys
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

_PROJECT_ROOT = re.search(r"^(.*gansu-livestock)", __file__).group(1)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from spider.gov_spider import BaseSpider


class PingliangSpider(BaseSpider):
    """平凉红牛价格指数月报爬虫（月更）"""

    NAME = "pingliang"
    # 东方财富文章搜索接口（JSONP 返回，服务端渲染，无 JS 挑战）
    SEARCH_API = "https://search-api-web.eastmoney.com/search/jsonp"
    KEYWORD = "平凉红牛价格指数"
    UA = "gansu-livestock-research/1.0"

    def __init__(self):
        super().__init__()
        self.session.headers["User-Agent"] = self.UA

    def _get(self, url, **kwargs):
        """固定 3 秒间隔的 GET（任务硬约束）"""
        time.sleep(3)
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp

    # 标题中的期号月份，如 （2026.8.1-8.31）
    RE_PERIOD = re.compile(r"（(\d{4})\.(\d{1,2})\.(\d{1,2})-")
    # 截至2026年8月31日，活牛价格指数报931.27点，较前一期上涨4.98%，价格报16.01元／斤
    RE_CATTLE = re.compile(
        r"活牛价格指数报(\d+\.?\d*)点[，,].{0,40}?价格报(\d+\.?\d*)元[／/]斤")
    # S级胴体价格指数报1873.24点，较前一期下跌2.21%，S级胴体价格报66.5元／斤
    RE_CARCASS = re.compile(
        r"S级胴体价格指数报(\d+\.?\d*)点[，,].{0,60}?S级胴体价格报(\d+\.?\d*)元[／/]斤")
    # 截至2026年8月31日 / 截至6月30日（部分期数省略年份，年份取标题期号）
    RE_ASOF = re.compile(r"截至(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日")

    def fetch_list(self):
        """调搜索接口，返回标题含'月报'的文章 [{url, title, date}]"""
        param = {
            "uid": "", "keyword": self.KEYWORD, "type": ["cmsArticleWebOld"],
            "client": "web", "clientVersion": "curr", "clientType": "web",
            "param": {"cmsArticleWebOld": {
                "searchScope": "default", "sort": "default", "pageIndex": 1,
                "pageSize": 20, "preTag": "", "postTag": ""}},
        }
        url = self.SEARCH_API + "?cb=cb&param=" + urllib.parse.quote(
            json.dumps(param, ensure_ascii=False))
        r = self._get(url)
        r.raise_for_status()
        body = r.text
        if body.startswith("cb("):
            body = body[3:body.rfind(")")]
        data = json.loads(body)
        arts = data.get("result", {}).get("cmsArticleWebOld", [])
        reports = []
        for a in arts:
            title = (a.get("title") or "").strip()
            if "月报" not in title:
                continue
            reports.append({
                "url": a.get("url", ""),
                "title": title,
                "date": (a.get("date") or "")[:10],
            })
        self.log("搜索到 %d 篇平凉红牛月报" % len(reports))
        return reports

    def parse_report(self, url):
        """抓正文，提取活牛价格/指数 + S级胴体价格/指数"""
        r = self._get(url)
        r.raise_for_status()
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "lxml")
        body = soup.find("div", id="ContentBody") or soup.find("article")
        if not body:
            self.log("WARN 正文容器缺失: %s" % url)
            return None
        text = body.get_text("\n", strip=True)

        m_cattle = self.RE_CATTLE.search(text)
        if not m_cattle:
            self.log("WARN 未匹配到活牛指数行: %s" % url)
            return None
        cattle_index = float(m_cattle.group(1))
        cattle_price = float(m_cattle.group(2))

        # 日期：优先正文"截至(年)月日"，缺年份时用标题期号年；最后回退标题期号起始日
        m_asof = self.RE_ASOF.search(text)
        m_period = self.RE_PERIOD.search(soup.title.get_text() if soup.title else "")
        if m_asof:
            year = m_asof.group(1) or (m_period.group(1) if m_period else None)
            if year:
                record = "%s-%02d-%02d" % (year, int(m_asof.group(2)),
                                           int(m_asof.group(3)))
            else:
                record = None
        elif m_period:
            record = "%s-%02d-%02d" % (m_period.group(1), int(m_period.group(2)),
                                       int(m_period.group(3)))
        else:
            record = None
        if not record:
            self.log("WARN 未匹配到日期: %s" % url)
            return None

        remark = "活牛价格指数报%.2f点" % cattle_index
        m_carcass = self.RE_CARCASS.search(text)
        if m_carcass:
            remark += "；S级胴体价格指数报%s点，价格报%s元/斤" % (
                m_carcass.group(1), m_carcass.group(2))

        return self.make_record(
            region="平凉市",
            category="活牛",
            price=cattle_price,
            unit="元/斤",
            date=record,
            source="index",
            source_detail="新华·中国平凉红牛价格指数（中国经济信息社）",
            report_title=soup.title.get_text(strip=True).split("_")[0].strip()
            if soup.title else url,
            remark=remark,
        )

    def run(self, max_reports=3):
        """抓最近 max_reports 期月报"""
        records = []
        reports = self.fetch_list()
        for item in reports[:max_reports]:
            try:
                rec = self.parse_report(item["url"])
                if rec:
                    records.append(rec)
                    self.log("OK %s 活牛%s元/斤 (%s)" % (
                        item["date"], rec["price"], rec["date"]))
            except Exception as e:
                self.log("FAIL %s: %s" % (item["url"], e))
            time.sleep(1)
        self.log("共获取 %d 期月报" % len(records))
        return records


if __name__ == "__main__":
    spider = PingliangSpider()
    for rec in spider.run(3):
        print(json.dumps(rec, ensure_ascii=False))
