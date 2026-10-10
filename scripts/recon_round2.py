# -*- coding: utf-8 -*-
"""第二轮侦察：修正域名探测 + 重点源深挖目标页"""
import time

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "gansu-livestock-research/1.0",
      "Accept-Language": "zh-CN,zh;q=0.9"}

def get(url):
    r = requests.get(url, headers=UA, timeout=18)
    r.encoding = r.apparent_encoding or "utf-8"
    return r

def show_links(url, patterns, limit=12):
    """列出页面中含指定关键词的链接"""
    r = get(url)
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    out = []
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if not t or t in seen:
            continue
        if any(p in t for p in patterns):
            seen.add(t)
            out.append((t[:45], a["href"][:90]))
            if len(out) >= limit:
                break
    return r.status_code, out

print("== A. 修正域名 ==")
for name, url in [("武威", "https://www.gswuwei.gov.cn/"),
                  ("庆阳", "https://zgqingyang.gov.cn/"),
                  ("甘南州", "http://www.gnzrmzf.gov.cn/")]:
    try:
        r = get(url)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "(无标题)"
        print("%s: HTTP %s | %s | len=%d" % (name, r.status_code, title[:35], len(r.text)))
    except Exception as e:
        print("%s: %s" % (name, str(e)[:60]))
    time.sleep(3)

print()
print("== B. 平凉门户: 牛/价格相关链接 ==")
try:
    code, links = show_links("http://www.pingliang.gov.cn/", ["牛", "价格", "畜牧"])
    print("HTTP", code)
    for t, h in links:
        print("  ", t, "->", h)
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== C. 临夏门户: 牛/羊相关链接 ==")
try:
    code, links = show_links("http://www.linxia.gov.cn/", ["牛", "羊", "畜牧", "价格"])
    print("HTTP", code)
    for t, h in links:
        print("  ", t, "->", h)
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== D. 张掖 xmj 频道: 牛/羊专栏链接 ==")
try:
    code, links = show_links("http://www.zhangye.gov.cn/xmj/index.html", ["牛", "羊"])
    print("HTTP", code)
    for t, h in links:
        print("  ", t, "->", h)
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== E. 惠农网: 牛/羊行情入口 ==")
try:
    code, links = show_links("https://www.cnhnb.com/", ["牛", "羊"], limit=15)
    print("HTTP", code)
    for t, h in links:
        print("  ", t, "->", h)
except Exception as e:
    print("异常:", str(e)[:70])
time.sleep(3)

print()
print("== F. 新华财经: 平凉红牛 ==")
try:
    r = get("https://www.cnfin.com/")
    soup = BeautifulSoup(r.text, "lxml")
    for a in soup.find_all("a", href=True):
        t = a.get_text(strip=True)
        if "红牛" in t or "平凉" in t:
            print("  ", t[:40], "->", a["href"][:90])
except Exception as e:
    print("异常:", str(e)[:70])
