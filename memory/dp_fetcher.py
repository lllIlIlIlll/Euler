"""DrissionPage SessionPage 批量抓取模板(V4 实测可用)。

用法:
    from memory.dp_fetcher import BatchFetcher
    fetcher = BatchFetcher(timeout=20, retry=1, ua='...')
    results, errors = fetcher.fetch([
        'https://www.state.gov/',
        'https://www.csis.org/',
    ], extract_fn=lambda page, url: {'title': page.title})
"""
import re, json, time
from datetime import datetime
from DrissionPage import SessionPage

DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# 元数据正则(覆盖 ISO / 美式 / 斜杠 三类日期)
DATE_PATTERNS = [
    r'20\d{2}-\d{2}-\d{2}',
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},?\s*20\d{2}',
    r'20\d{2}/\d{2}/\d{2}',
]


class BatchFetcher:
    def __init__(self, timeout=20, retry=1, ua=DEFAULT_UA):
        self.p = SessionPage()
        self.p.timeout = timeout
        self.p.retry_times = retry
        self.p.retry_interval = 2
        self.p.user_agent = ua

    def fetch(self, urls, extract_fn=None):
        """extract_fn(page, url) -> dict  (可选,默认提取 title+date_hits)"""
        results, errors = [], []
        for i, url in enumerate(urls, 1):
            entry = {'url': url, 'fetched_at': time.time()}
            try:
                ok = self.p.get(url)
                if not ok:
                    entry['status'] = 0
                    entry['error'] = 'get() returned False'
                    errors.append(entry)
                    print(f"[{i:2}/{len(urls)}] {url[:55]:<55} -> FAIL")
                    continue
                entry['status'] = self.p.response.status_code if self.p.response else 0
                entry['html_len'] = len(self.p.html or '')
                if extract_fn:
                    entry.update(extract_fn(self.p, url))
                else:
                    entry['title'] = self.p.title
                    entry['date_hits'] = self._scrape_dates(self.p.html or '')
                results.append(entry)
                print(f"[{i:2}/{len(urls)}] {url[:55]:<55} -> {entry['status']}")
            except Exception as e:
                entry['error'] = str(e)[:120]
                errors.append(entry)
                print(f"[{i:2}/{len(urls)}] {url[:55]:<55} -> ERR: {str(e)[:50]}")
        return results, errors

    def _scrape_dates(self, html):
        hits = []
        for pat in DATE_PATTERNS:
            hits.extend(re.findall(pat, html)[:5])
        # 去重保序
        seen, out = set(), []
        for h in hits:
            if h not in seen:
                seen.add(h)
                out.append(h)
        return out[:8]

    def save(self, results, errors, path):
        payload = {
            'results': results,
            'errors': errors,
            'fetched_at': time.time(),
            'iso': datetime.fromtimestamp(time.time()).isoformat(timespec='seconds'),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return payload


if __name__ == '__main__':
    import sys
    urls = sys.argv[1:] or ['https://www.state.gov/', 'https://www.csis.org/']
    f = BatchFetcher()
    r, e = f.fetch(urls)
    f.save(r, e, 'dp_fetch.json')
    print(f"\nOK={len(r)} ERR={len(e)}")
