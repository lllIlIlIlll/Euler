"""Bing News多查询批量抓取 - 复用 daily_report SOP
- 用Playwright evaluate 直接拿卡片数据(DOM的algo+title+snippet+url+time)
- 不依赖HTML regex截断,跳过3000字符窗限制
- 15个查询分批执行,每批5个
- 输出 {query_key: [{title,url,snippet,source,rel_time},...], ...} 到 ./{outfile}.json
- 用法: 修改 QUERIES, OUTFILE, 调用 main()
"""
import json, time, os
from playwright.sync_api import sync_playwright

QUERIES = [
    ("S1_rare_earth",    "China rare earth export controls June 2026"),
    ("S1_crit_minerals", "USGS critical minerals 2026 list update"),
    ("S2_biosafety",     "WHO biosafety pandemic June 2026"),
    ("S2_drug",          "FDA drug shortage June 2026"),
    ("S3_food",          "FAO food price index June 2026"),
    ("S3_wfp",           "WFP emergency operation Sudan June 2026"),
    ("S4_water",         "UN water scarcity crisis June 2026"),
    ("S4_deepsea",       "deep sea mining moratorium ISA 2026"),
    ("S1_magnet",        "rare earth magnet supply chain June 2026"),
    ("S5_oil",           "OPEC production cut June 2026"),
    ("S5_iran",          "Iran nuclear stockpile June 2026"),
    ("S6_climate",       "WMO climate extreme weather June 2026"),
    ("S2_mpox",          "WHO mpox outbreak 2026"),
    ("S7_cyber",         "CISA cyber attack June 2026"),
    ("S9_migration",     "IOM migration June 2026"),
]

BATCH = 5
OUTFILE = './bing_raw_YYYYMMDD.json'

CARD_JS = r"""
() => {
    const out = [];
    const cards = document.querySelectorAll('div.algo, li.b_algo, div.news-card, [class*="card"]');
    for (const c of cards) {
        const a = c.querySelector('a[href]');
        if (!a || !/^https?:/.test(a.href)) continue;
        const title = a.innerText.trim();
        const url = a.href;
        const snippet = (c.innerText || '').slice(0, 600);
        const timeMatch = (c.innerText || '').match(/(\d+\s*(?:min|hour|hr|h|d|day|week|w|month|mon|year|y|yr)s?)\s*ago/i)
                       || (c.innerText || '').match(/\b(\d+(?:min|h|d|w|mon|y))\b/i);
        const rel = timeMatch ? timeMatch[0] : '';
        const srcEl = c.querySelector('[class*="source"], cite, .b_attribution');
        const src = srcEl ? srcEl.innerText.trim() : '';
        out.push({title, url, snippet, source: src, rel_time: rel});
    }
    return out;
}
"""

def main():
    all_results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox','--disable-blink-features=AutomationControlled'])
        ctx = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36')
        for i in range(0, len(QUERIES), BATCH):
            batch = QUERIES[i:i+BATCH]
            page = ctx.new_page()
            for key, q in batch:
                url = f'https://www.bing.com/news/search?q={q.replace(" ","+")}&qft=interval%3d"7"'
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(2500)
                    data = page.evaluate(CARD_JS)
                    all_results[key] = data
                    with_time = sum(1 for c in data if c.get('rel_time'))
                    print(f'[{key}] {q} -> {len(data)} cards, {with_time} with time')
                except Exception as e:
                    print(f'[{key}] FAIL: {e}')
                    all_results[key] = []
            page.close()
        browser.close()
    with open(OUTFILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in all_results.values())
    timed = sum(sum(1 for c in v if c.get('rel_time')) for v in all_results.values())
    print(f'\nTOTAL: {total} cards, {timed} with time -> {OUTFILE}')

if __name__ == '__main__':
    main()
