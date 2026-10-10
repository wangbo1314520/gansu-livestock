# -*- coding: utf-8 -*-
"""
数据源侦察：只读访问各源首页，记录 可访问性/编码/标题/牛羊关键词
请求间隔 3 秒，UA = gansu-livestock-research/1.0
"""
import re
import time

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "gansu-livestock-research/1.0",
      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
      "Accept-Language": "zh-CN,zh;q=0.9"}

SOURCES = [
    ("1", "甘肃省畜牧兽医局", "http://xmsy.gansu.gov.cn/"),
    ("2", "甘肃省农业农村厅", "http://nync.gansu.gov.cn/"),
    ("3a", "省发改委价格监测(fgw域名)", "http://fgw.gansu.gov.cn/"),
    ("3b", "省发改委(fzgg域名,已知WAF)", "http://fzgg.gansu.gov.cn/"),
    ("4", "省商务厅(已知WAF)", "https://swt.gansu.gov.cn/"),
    ("5", "武威市政府门户", "http://www.wuwei.gov.cn/"),
    ("6", "平凉市政府门户", "http://www.pingliang.gov.cn/"),
    ("7", "庆阳市政府门户", "http://www.qingyang.gov.cn/"),
    ("8", "临夏州政府门户", "http://www.linxia.gov.cn/"),
    ("9", "甘南州政府门户", "http://www.gannan.gov.cn/"),
    ("10", "张掖畜牧兽医局频道", "http://www.zhangye.gov.cn/xmj/index.html"),
    ("11", "新华财经(平凉红牛指数)", "https://www.cnfin.com/"),
    ("12", "惠农网", "https://www.cnhnb.com/"),
    ("13", "中国畜牧兽医信息网", "http://www.cav.net.cn/"),
    ("14", "农业农村部", "http://www.moa.gov.cn/"),
    ("15", "张掖市政府门户首页", "http://www.zhangye.gov.cn/"),
]

KEYWORDS = ["牛", "羊", "价格", "行情", "监测", "活牛", "活羊", "牛肉", "羊肉"]


def probe(name, url):
    try:
        r = requests.get(url, headers=UA, timeout=15, allow_redirects=True)
        enc = r.apparent_encoding or "-"
        r.encoding = enc
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "(无标题)"
        text = soup.get_text()
        kw = {k: text.count(k) for k in KEYWORDS if text.count(k) > 0}
        links = [a.get("href") for a in soup.find_all("a", href=True)
                 if a.get_text(strip=True) and any(
                     k in a.get_text(strip=True) for k in ("牛", "羊", "价格", "行情", "监测"))]
        return "HTTP %s | enc=%s | title=%s | len=%d | kw=%s | 候选链接%d" % (
            r.status_code, enc, title[:40], len(r.text), kw, len(links))
    except requests.exceptions.Timeout:
        return "超时"
    except requests.exceptions.ConnectionError as e:
        return "连接失败(%s)" % str(e)[:50]
    except Exception as e:
        return "异常(%s)" % str(e)[:50]


if __name__ == "__main__":
    for sid, name, url in SOURCES:
        print("[%s] %s %s" % (sid, name, url))
        print("   ", probe(name, url))
        time.sleep(3)
