from typing import List, Dict
from application.repositories import debunks_repo as repo


def get_today_debunks(limit: int = 6, url: str = 'https://www.piyao.org.cn') -> List:
    limit = max(1, min(int(limit or 6), 50))
    html = repo.fetch_html(url)
    data = repo.parse_today_section(html, base_url=url, max_items=limit)
    if not data:
        return []
    rows = [data.get('title')]
    for it in (data.get('items') or [])[:limit]:
        rows.append({
            'title': it.get('title'),
            'link': it.get('link'),
        })
    return rows


def get_union_debunks(limit: int = 6, url: str = 'https://www.piyao.org.cn') -> List:
    limit = max(1, min(int(limit or 6), 50))
    html = repo.fetch_html(url)
    data = repo.parse_lianhe_section(html, base_url=url, max_items=limit)
    if not data:
        return []
    rows = [data.get('title')]
    for it in (data.get('items') or [])[:limit]:
        rows.append({
            'title': it.get('title'),
            'link': it.get('link'),
        })
    return rows

