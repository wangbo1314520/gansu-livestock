# -*- coding: utf-8 -*-
"""第四轮增补侦察：卓创/金投 + 惠农网羊细分 + 甘南/临夏牦牛 + 庆阳/武威畜牧频道"""
import time

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "gansu-livestock-research/1.0",
      "Accept-Language": "zh-CN,zh;q=0.9"}

def get(url):
    r = requests.get(url, headers=UA, timeout=15)
    r.encoding = r.apparent_encoding or "utf-8"
    return r

print("== 15a. 卓创资讯畜牧频道 ==")
for url in ["https://www.sci99.com/", "https://www.sci99.com/xumu/"]:
    try:
        r = get(url)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "(无)"
        print(url, "-> HTTP", r.status_code, "|", title[:40], "| len", len(r.text))
    except Exception as e:
        print(url, "->", str(e)[:60])
    time.sleep(3)

print()
print("== 15b. 金投网畜牧/农产品频道 ==")
for url in ["https://www.cngold.org/", "https://nongye.cngold.org/"]:
    try:
        r = get(url)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "(无)"
        print(url, "-> HTTP", r.status_code, "|", title[:40], "| len", len(r.text))
    except Exception as e:
        print(url, "->", str(e)[:60])
    time.sleep(3)

print()
print("== 12b. 惠农网 活羊页：找母羊/羊羔/育肥羊细分 ==")
try:
    r = get("https://www.cnhnb.com/p/yang/")
    soup = BeautifulSoup(r.text, "lxml")
    print("HTTP", r.status_code, "| len", len(r.text))
    text = soup.get_text()
    for kw in ["羊羔", "羔羊", "母羊", "基础母羊", "育肥羊", "波尔山羊", "小尾寒羊", "湖羊", "牦牛", "黄牛"]:
        cnt = text.count(kw)
        if cnt:
            print("   关键词 '%s': %d 次" % (kw, cnt))
    # 列羊相关品类链接
    seen = set()
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if t and ("/p/" in a["href"]) and any(k in t for k in ("羊", "牛")) and t not in seen:
            seen.add(t)
            print("   品类:", t[:20], "->", a["href"][:50])
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== 9b. 甘南州门户：搜牦牛/价格 ==")
try:
    r = get("http://www.gnzrmzf.gov.cn/")
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    found = 0
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if not t or t in seen:
            continue
        if any(k in t for k in ("牦牛", "畜牧", "农", "价格")):
            seen.add(t)
            print("  ", t[:40], "->", a["href"][:70])
            found += 1
            if found >= 10:
                break
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== 8b. 临夏州门户：搜牦牛/羊/畜牧 ==")
try:
    r = get("http://www.linxia.gov.cn/")
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    found = 0
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if not t or t in seen:
            continue
        if any(k in t for k in ("牦牛", "畜牧", "羊", "价格")):
            seen.add(t)
            print("  ", t[:40], "->", a["href"][:70])
            found += 1
            if found >= 10:
                break
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== 5b. 武威门户：找农业农村/畜牧频道入口 ==")
try:
    r = get("https://www.gswuwei.gov.cn/")
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if not t or t in seen:
            continue
        if any(k in t for k in ("畜牧", "农业农村", "农牧")):
            seen.add(t)
            print("  ", t[:40], "->", a["href"][:70])
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== 7b. 庆阳门户：找农业农村/畜牧频道入口 ==")
try:
    r = get("https://zgqingyang.gov.cn/")
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if not t or t in seen:
            continue
        if any(k in t for k in ("畜牧", "农业农村", "农牧", "牛", "羊")):
            seen.add(t)
            print("  ", t[:40], "->", a["href"][:70])
except Exception as e:
    print("异常:", str(e)[:70])
