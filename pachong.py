#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一个极简的验证用爬虫：尝试从 https://www.piyao.org.cn 抓取“今日辟谣”标题与列表条目。
不依赖数据库，仅使用 requests + BeautifulSoup。

用法：
  python3 pachong.py
可选：
  python3 pachong.py --url https://www.piyao.org.cn
"""
import sys
import re
import argparse
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.piyao.org.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.piyao.org.cn/",
}


def fetch_html(url: str, timeout: int = 20) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def extract_date_from_title(title: str) -> str:
    """从“今日辟谣（YYYY年MM月DD日）”中提取原始中文日期字符串与 ISO 格式。
    返回 (cn_date_str, iso_str)；若未匹配到，返回 ("", "").
    """
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", title)
    if not m:
        return "", ""
    y, mo, d = m.groups()
    cn = f"{y}年{mo}月{d}日"
    iso = f"{int(y):04d}-{int(mo):02d}-{int(d):02d} 08:00:00"
    return cn, iso


def parse_today_section(html: str, base_url: str = BASE_URL, max_items: int = 10):
    """解析页面中的“今日辟谣”区块，返回：
    {
      'title': '今日辟谣（2025年12月5日）',
      'date_cn': '2025年12月5日',
      'date_iso': '2025-12-05 08:00:00',
      'items': [ {'title': '12306回应取消靠窗选座', 'link': 'https://...'}, ... ]
    }
    若未解析到，返回 None。
    """
    soup = BeautifulSoup(html, "lxml")

    # 找包含“今日辟谣”的 h2（一般 h2 里有 a 标签）
    h2_list = [h for h in soup.find_all("h2") if "今日辟谣" in h.get_text(strip=True)]
    for h2 in h2_list:
        a = h2.find("a")
        title_text = (a.get_text(strip=True) if a else h2.get_text(strip=True))
        date_cn, date_iso = extract_date_from_title(title_text)

        # h2 后面最近的 ul 列表
        ul = h2.find_next("ul")
        if not ul:
            continue

        items = []
        li_list = ul.find_all("li")
        for li in li_list:
            link_el = li.find("a", href=True)
            if not link_el:
                continue
            t = link_el.get_text(strip=True)
            href = link_el["href"]
            full_link = href if href.startswith("http") else urljoin(base_url, href)
            if t:
                items.append({"title": t, "link": full_link})
            if len(items) >= max_items:
                break

        if items:
            return {
                "title": title_text,
                "date_cn": date_cn,
                "date_iso": date_iso,
                "items": items,
            }

    return None

def parse_LianHePiYao(html: str, base_url: str = BASE_URL, max_items: int = 10):
    soup = BeautifulSoup(html, "lxml")

    # 找包含“今日辟谣”的 h2（一般 h2 里有 a 标签）
    h2_list = [h for h in soup.find_all("h2") 
           if h.get_text(strip=True).startswith("中国互联网联合辟谣平台")]
    for h2 in h2_list:
        a = h2.find("a")
        title_text = (a.get_text(strip=True) if a else h2.get_text(strip=True))
        date_cn, date_iso = extract_date_from_title(title_text)

        # h2 后面最近的 ul 列表
        ul = h2.find_next("ul")
        if not ul:
            continue

        items = []
        li_list = ul.find_all("li")
        for li in li_list:
            link_el = li.find("a", href=True)
            if not link_el:
                continue
            t = link_el.get_text(strip=True)
            href = link_el["href"]
            full_link = href if href.startswith("http") else urljoin(base_url, href)
            if t:
                items.append({"title": t, "link": full_link})
            if len(items) >= max_items:
                break

        if items:
            return {
                "title": title_text,
                "date_cn": date_cn,
                "date_iso": date_iso,
                "items": items,
            }

    return None

def main():
    ap = argparse.ArgumentParser(description="验证抓取皮皮谣‘今日辟谣’区块")
    ap.add_argument("--url", default=BASE_URL, help="要抓取的页面（默认首页）")
    ap.add_argument("--max", type=int, default=10, help="最多展示的条目数")
    args = ap.parse_args()

    # 尝试多个入口（有些时候 index.htm 更稳定）
    candidates = [args.url]
    if args.url.rstrip("/") == BASE_URL:
        candidates.append(urljoin(BASE_URL, "index.htm"))

    last_error = None
    for url in candidates:
        try:
            print(f"请求: {url}")
            html = fetch_html(url)
            print(f"页面长度: {len(html)} 字符")
            data = parse_LianHePiYao(html, max_items=args.max)
            if not data:
                print("未在页面中解析到‘今日辟谣’区块，换下一个候选 URL 试试...")
                continue

            print("\n===== 解析结果 =====")
            if data["date_cn"]:
                print(f"{data['title']}  (ISO: {data['date_iso']})")
            else:
                print(data["title"])  # 没解析到日期也打印标题
            for i, it in enumerate(data["items"], 1):
                print(f"{i}. {it['title']} -> {it['link']}")
            print("===================\n")
            print("抓取成功 ✅")
            return 0
        except Exception as e:
            last_error = e
            print(f"抓取失败: {e}")

    print("所有候选 URL 均未能成功解析 ‘今日辟谣’ 区块 ❌")
    if last_error:
        print(f"最后一个错误: {last_error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

