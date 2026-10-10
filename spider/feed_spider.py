# -*- coding: utf-8 -*-
"""
饲料价格爬虫框架：玉米、豆粕、麸皮、苜蓿草

数据源（需求文档 3.4）：
  - 惠农网行情（日，TODO 确认 API 或页面）
  - 甘肃当地饲料经销商报价页（TODO）

输出与 gov_spider 相同的标准记录，category 为饲料名。
"""
import datetime

from spider.gov_spider import REQUEST_INTERVAL, RECORD_TEMPLATE, BaseSpider


class FeedSpider(BaseSpider):
    """饲料价格爬虫"""

    FEEDS = ["玉米", "豆粕", "麸皮", "苜蓿草"]

    # TODO: 联调阶段填入真实地址与参数
    SOURCES = [
        {"name": "惠农网-玉米行情", "url": None, "api": False},
        {"name": "惠农网-豆粕行情", "url": None, "api": False},
        {"name": "当地经销商报价", "url": None, "api": False},
    ]

    def fetch_api(self, source):
        """API 型数据源：直接请求 JSON 接口"""
        if not source["url"]:
            self.log("跳过 %s：URL 未配置（TODO）" % source["name"])
            return []
        resp = self.get(source["url"])
        data = resp.json()
        # TODO: 按接口实际结构解析，示例：
        # for item in data["data"]["list"]:
        #     records.append(self.make_record(
        #         region=item.get("province", "甘肃省"),
        #         category=item["productName"], price=float(item["price"]),
        #         date=item["date"], source="market", source_detail=source["name"]))
        self.log("%s API 返回 %d 条" % (source["name"], len(data) if isinstance(data, list) else 0))
        return []

    def fetch_page(self, source):
        """页面型数据源：解析 HTML 表格"""
        if not source["url"]:
            self.log("跳过 %s：URL 未配置（TODO）" % source["name"])
            return []
        from bs4 import BeautifulSoup
        resp = self.get(source["url"])
        soup = BeautifulSoup(resp.text, "lxml")
        records = []
        # TODO: 按页面结构解析价格表格
        self.log("%s 页面解析 %d 条" % (source["name"], len(records)))
        return records

    def run(self):
        all_records = []
        for source in self.SOURCES:
            try:
                if source.get("api"):
                    all_records.extend(self.fetch_api(source))
                else:
                    all_records.extend(self.fetch_page(source))
            except Exception as e:
                self.log("%s 抓取失败: %s" % (source["name"], e))
        self.log("本次共抓取 %d 条饲料价格" % len(all_records))
        return all_records


if __name__ == "__main__":
    spider = FeedSpider()
    data = spider.run()
    import json
    import os
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "raw")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "feed_%s.json" % datetime.date.today().strftime("%Y%m%d"))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("原始数据已保存:", out)
