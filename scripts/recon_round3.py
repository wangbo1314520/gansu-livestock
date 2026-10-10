# -*- coding: utf-8 -*-
"""第三轮定点确认：平凉畜牧局官网 / 平凉价格文章 / 惠农网牛行情页"""
import time

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "gansu-livestock-research/1.0",
      "Accept-Language": "zh-CN,zh;q=0.9"}

def get(url):
    r = requests.get(url, headers=UA, timeout=18)
    r.encoding = r.apparent_encoding or "utf-8"
    return r

print("== 1. 平凉市畜牧兽医局 xmsy.pingliang.gov.cn ==")
try:
    r = get("http://xmsy.pingliang.gov.cn/")
    soup = BeautifulSoup(r.text, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else "(无标题)"
    print("HTTP %s | %s | len=%d" % (r.status_code, title, len(r.text)))
    seen = set()
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if not t or t in seen or len(t) < 8:
            continue
        if any(k in t for k in ("牛", "羊", "价格", "行情", "监测", "周报")):
            seen.add(t)
            print("  ", t[:50], "->", a["href"][:85])
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== 2. 平凉 八月份重要商品价格变动文章（看是否含牛羊）==")
try:
    r = get("http://www.pingliang.gov.cn/cxzx/gysy/art/2025/art_8f8e076156a94134bbb44ee36f5a30e9.html")
    soup = BeautifulSoup(r.text, "lxml")
    text = soup.body.get_text("\n", strip=True)
    # 找正文段（含"价格"上下文）
    idx = text.find("变动情况")
    seg = text[idx:idx + 900] if idx >= 0 else text[:900]
    print("HTTP", r.status_code)
    print(seg[:900])
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== 3. 惠农网 牛 行情页 /p/niu/ ==")
try:
    r = get("https://www.cnhnb.com/p/niu/")
    soup = BeautifulSoup(r.text, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else "(无标题)"
    print("HTTP %s | %s | len=%d" % (r.status_code, title, len(r.text)))
    # 找价格元素
    import re
    prices = re.findall(r"(牛[^<>{}]{0,12}?)\s*(?:￥|¥|<[^>]*>)*\s*(\d+(?:\.\d+)?)\s*元?/(斤|kg|公斤)", r.text)
    text = soup.get_text()
    # 抓含"元/"的价格行样例
    samples = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9（）()]{2,18}[：:]?\s*[¥￥]?\d+(?:\.\d+)?\s*元/(斤|kg|公斤|头)", text)
    for s in list(dict.fromkeys(samples))[:6]:
        print("   价格形态样例:", s)
    # 产地甘肃的条目
    gs = re.findall(r"甘肃[\u4e00-\u9fa5]{0,6}", text)
    print("   提及甘肃的条目数:", len(gs), list(dict.fromkeys(gs))[:5])
except Exception as e:
    print("异常:", str(e)[:70])
