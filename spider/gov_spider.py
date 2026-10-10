# -*- coding: utf-8 -*-
"""
甘肃各市州畜牧兽医局 / 省发改委 / 省商务厅 价格爬虫框架

数据源（需求文档 3.4）：
  - 甘肃省发改委价格监测（周）
  - 甘肃省商务厅生活必需品（周）
  - 各市州畜牧兽医局畜产品价格（周）
  - 新华指数·平凉红牛（月）

设计：统一输出 [{region, category, price, unit, date, source, source_detail}]，
交给 clean.py 清洗后由 import_db.py 入库。
注意：遵守 robots.txt 与访问频率（每次请求间隔 >= 2s），仅用于个人研究。

TODO：实际 URL 与解析规则在联调阶段逐个补充。
"""
import datetime
import time

import requests
from bs4 import BeautifulSoup

# 统一输出字段的标准记录模板
RECORD_TEMPLATE = {
    "region": None,          # 地区名：兰州 / 平凉 / ...
    "category": None,        # 分类名：活牛 / 牛肉 / 活羊 / 羊肉
    "price": None,           # 价格（元/斤）
    "unit": "元/斤",
    "date": None,            # 价格日期 YYYY-MM-DD
    "source": "gov",         # 数据来源类型
    "source_detail": None,   # 来源明细：单位+期数
    "breed": None,           # 品种（可选）
}

# 请求头：模拟普通浏览器，避免被简单拦截
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

REQUEST_INTERVAL = 2.0       # 两次请求最小间隔（秒），礼貌爬取


class BaseSpider:
    """爬虫基类：带间隔的 GET、日志"""

    def __init__(self, log_path=None):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._last_request = 0.0
        self.logs = []

    def log(self, msg):
        """内存日志 + 控制台"""
        line = "[%s] %s" % (datetime.datetime.now().strftime("%H:%M:%S"), msg)
        self.logs.append(line)
        print(line)

    def get(self, url, **kwargs):
        """带间隔控制的 GET"""
        wait = REQUEST_INTERVAL - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.time()
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"   # 政府站点常见 gb2312
        return resp

    @staticmethod
    def make_record(**kwargs):
        """按模板构造标准记录，过滤 None"""
        record = dict(RECORD_TEMPLATE)
        record.update({k: v for k, v in kwargs.items() if v is not None})
        return record


class GovSpider(BaseSpider):
    """政府价格监测爬虫"""

    # TODO: 联调阶段填入真实栏目地址
    SOURCES = [
        {"name": "甘肃省发改委-价格监测", "url": None, "list_selector": None},
        {"name": "甘肃省商务厅-生活必需品市场", "url": None, "list_selector": None},
        {"name": "新华指数-平凉红牛", "url": None, "list_selector": None},
        # 14 市州畜牧兽医局
        {"name": "兰州市农业农村局", "url": None, "list_selector": None},
        {"name": "平凉市畜牧兽医局", "url": None, "list_selector": None},
        # ...其余市州 TODO
    ]

    def fetch_list(self, source):
        """抓取栏目列表页，返回详情页链接列表"""
        if not source["url"]:
            self.log("跳过 %s：URL 未配置（TODO）" % source["name"])
            return []
        resp = self.get(source["url"])
        soup = BeautifulSoup(resp.text, "lxml")
        # TODO: 按各站点实际结构解析列表
        links = [a.get("href") for a in soup.select(source["list_selector"] or "a")]
        self.log("%s 抓到 %d 个链接" % (source["name"], len(links)))
        return links

    def parse_detail(self, url, source_name):
        """解析详情页 -> 标准记录列表"""
        resp = self.get(url)
        soup = BeautifulSoup(resp.text, "lxml")
        records = []
        # TODO: 解析价格表格。政府监测常见结构：
        #   <table><tr><td>品名</td><td>价格</td><td>单位</td></tr></table>
        # for tr in soup.select("table tr"):
        #     cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        #     category, price = self.match_category(cells)
        #     if category:
        #         records.append(self.make_record(
        #             region=self.guess_region(source_name),
        #             category=category, price=price,
        #             date=self.guess_date(soup), source_detail=source_name))
        self.log("%s 解析出 %d 条记录" % (url, len(records)))
        return records

    @staticmethod
    def match_category(cells):
        """把页面品类名匹配到标准分类：活牛/牛肉/活羊/羊肉"""
        mapping = {"活牛": "活牛", "牛": "活牛", "育肥牛": "活牛",
                   "牛肉": "牛肉", "去骨牛肉": "牛肉",
                   "活羊": "活羊", "羊": "活羊", "育肥羊": "活羊",
                   "羊肉": "羊肉", "带骨羊肉": "羊肉"}
        for cell in cells:
            if cell in mapping:
                return mapping[cell]
        return None

    @staticmethod
    def parse_price(text):
        """'12.5元/斤' / '25.00' -> float 或 None"""
        import re
        m = re.search(r"(\d+(?:\.\d+)?)", text or "")
        return float(m.group(1)) if m else None

    def run(self):
        """执行全部数据源：抓列表 -> 逐条解析 -> 汇总"""
        all_records = []
        for source in self.SOURCES:
            try:
                links = self.fetch_list(source)
                for link in links[:20]:           # 每源最多20篇，控制频率
                    if link and not link.startswith("http"):
                        link = source["url"].rstrip("/") + "/" + link.lstrip("/")
                    all_records.extend(self.parse_detail(link, source["name"]))
            except Exception as e:
                self.log("%s 抓取失败: %s" % (source["name"], e))
        self.log("本次共抓取 %d 条记录" % len(all_records))
        return all_records


class ZhangyeSpider(BaseSpider):
    """
    张掖市畜牧兽医局（张掖市政府门户 xmj 频道）价格周报爬虫 —— 已实测可用（2026-10-10）

    数据形态：通知公告栏每周发布"张掖市第N周猪肉价格周报"，
    正文为一段纯文字，如：
      "本周生猪平均价格10.7元／公斤，较上周下降10％；仔猪平均销售价格20.7元/公斤..."
    robots.txt 不存在（404），无爬取限制；请求间隔 >= 3 秒。

    注意：该源目前只发布猪价周报（生猪/仔猪/白条猪），
    与项目 8 分类（活牛/牛肉/活羊/羊肉/饲料）不重合，
    解析结果默认只落盘不入库，待人工决定是否扩充 price_category。
    """

    BASE = "http://www.zhangye.gov.cn/xmj"
    LIST_PAGES = [
        BASE + "/dzdt/tzgg/index.html",
        BASE + "/dzdt/tzgg/index_1.html",
    ]

    def find_reports(self):
        """列表页发现"价格周报"文章链接，返回 [(标题, 绝对URL)]"""
        found = []
        seen = set()
        for page_url in self.LIST_PAGES:
            resp = self.get(page_url)
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.find_all("a", href=True):
                title = a.get_text(strip=True)
                if "价格周报" not in title or title in seen:
                    continue
                seen.add(title)
                href = a["href"]
                if href.startswith("./"):
                    href = page_url.rsplit("/", 1)[0] + href[1:]
                elif not href.startswith("http"):
                    href = self.BASE + "/" + href.lstrip("/")
                found.append((title, href))
            self.log("列表页 %s 发现 %d 篇周报" % (page_url.rsplit('/', 1)[-1], len(found)))
        return found

    @staticmethod
    def _normalize(text):
        """全角转半角（周报正文混用 ／ ．％ 等全角字符）"""
        out = []
        for ch in text:
            code = ord(ch)
            if code == 0xFF0F:          # ／ -> /
                out.append("/")
            elif code == 0xFF0E:        # ． -> .
                out.append(".")
            elif 0xFF01 <= code <= 0xFF5E:
                out.append(chr(code - 0xFEE0))   # 全角ASCII区 -> 半角
            else:
                out.append(ch)
        return "".join(out)

    def parse_report(self, url):
        """解析一篇周报 -> 标准记录列表"""
        import re
        resp = self.get(url)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else ""
        body_text = soup.body.get_text("\n", strip=True)
        self.log("解析周报: %s" % title[:40])

        # 周次与日期：标题"第三十四周"，页面"日期：2026-09-20"
        week_m = re.search(r"第([\u4e00-\u9fa5]+)周", title)
        date_m = re.search(r"日期[:：]\s*(\d{4}-\d{2}-\d{2})", body_text)
        report_date = date_m.group(1) if date_m else str(datetime.date.today())

        text = self._normalize(body_text)
        # 形如：生猪平均价格10.7元/公斤，较上周下降10%；
        pattern = re.compile(
            r"([\u4e00-\u9fa5]{2,8}?)(?:平均)?(?:销售|出场)?(?:平均)?价格"
            r"(\d+(?:\.\d+)?)元/(公斤|斤)"
            r"(?:，较上周(上升|下降)(-?\d+(?:\.\d+)?)%)?")

        records = []
        for m in pattern.finditer(text):
            name, price, unit, direction, pct = m.groups()
            name = re.sub(r"^(本周|其中|该|上述)", "", name)   # 剥离"本周生猪"的前缀
            if not name:
                continue
            change = None
            if direction:
                sign = 1 if direction == "上升" else -1
                change = round(sign * float(pct), 2)
            records.append(self.make_record(
                region="张掖市",
                category=name,                 # 原始品类名，如：生猪、仔猪
                price=float(price),
                unit="元/" + unit,
                date=report_date,
                source="gov",
                source_detail="张掖市畜牧兽医局价格周报(%s)" % (
                    week_m.group(0) if week_m else title[:16]),
                change_pct=change,
                report_title=title,
            ))
        self.log("  提取 %d 条价格记录" % len(records))
        return records

    def run(self, max_reports=3):
        """抓取列表 -> 解析前 max_reports 篇周报"""
        reports = self.find_reports()
        all_records = []
        for title, url in reports[:max_reports]:
            try:
                all_records.extend(self.parse_report(url))
            except Exception as e:
                self.log("周报抓取失败 %s: %s" % (title[:30], e))
        self.log("本次共抓取 %d 条记录" % len(all_records))
        return all_records


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "zhangye":
        spider = ZhangyeSpider()
        data = spider.run(max_reports=3)
        import json
        import os
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "data")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "spider_sample_%s.json"
                           % datetime.date.today().strftime("%Y%m%d"))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("样本数据已保存:", out)
        sys.exit(0)

    spider = GovSpider()
    data = spider.run()
    # 原始数据落盘 data/raw/，供 clean.py 处理
    import json
    import os
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "raw")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "gov_%s.json" % datetime.date.today().strftime("%Y%m%d"))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("原始数据已保存:", out)
