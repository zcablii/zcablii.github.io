"""Fetch the public Scholar profile and generate live Shields.io endpoint data."""
import argparse
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urljoin
from urllib.request import Request, urlopen

PROFILE = 'https://scholar.google.com/citations?user=vKnUqmMAAAAJ&hl=en&pagesize=100'
REPO = Path(__file__).resolve().parents[1]


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = dict(attrs)
            self.current['text'] = ''

    def handle_data(self, text):
        if self.current is not None:
            self.current['text'] += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None


def normalize(title):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', title).lower())


def parse_profile(html):
    publications = []
    for row in re.findall(r'<tr\b[^>]*class="gsc_a_tr"[^>]*>(.*?)</tr>', html, re.S):
        parser = Anchors()
        parser.feed(row)
        title = next((a for a in parser.links if 'gsc_a_at' in a.get('class', '').split()), None)
        citations = next((a for a in parser.links if 'gsc_a_ac' in a.get('class', '').split()), None)
        if title is None or citations is None:
            raise ValueError('Incomplete Scholar publication row; refusing to publish partial data')
        match = re.search(r'citation_for_view=([^&]+)', title['href'])
        text = citations['text'].strip().replace(',', '')
        if text and not text.isdigit():
            raise ValueError(f'Unexpected citation count: {text!r}')
        publications.append({
            'title': title['text'].strip(),
            'scholar_id': match.group(1) if match else None,
            'scholar_url': urljoin(PROFILE, title['href']),
            'citations': int(text) if text else 0,
        })
    table = re.search(r'<table[^>]*id="gsc_rsb_st"[^>]*>(.*?)</table>', html, re.S)
    totals = re.findall(r'<td class="gsc_rsb_std">([\d,]+)</td>', table.group(1)) if table else []
    if len(publications) < 10 or len(totals) != 6:
        raise ValueError('Scholar returned an incomplete profile or a challenge page; keeping prior data')
    return publications, {'citations': int(totals[0].replace(',', '')), 'h_index': int(totals[2].replace(',', ''))}


def build_metrics(html, papers):
    rows, totals = parse_profile(html)
    by_id = {row['scholar_id']: row for row in rows}
    by_title = {normalize(row['title']): row for row in rows}
    data = {'updated': datetime.now(timezone.utc).isoformat(), 'source': PROFILE, 'totals': totals, 'publications': {}}
    matched = 0
    for paper in papers:
        row = by_id.get(paper.get('scholar_id'))
        if row is None:
            row = by_title.get(normalize(paper.get('scholar_title', paper['title'])))
        data['publications'][paper['id']] = {
            'title': paper['title'],
            'status': 'indexed' if row else 'pending',
            'citations': row['citations'] if row else None,
            'scholar_url': row['scholar_url'] if row else paper['scholar_url'],
        }
        matched += row is not None
    if matched < 8:
        raise ValueError(f'Only matched {matched} selected papers; keeping prior data')
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('results'))
    parser.add_argument('--html', type=Path, help='Use a saved profile response for offline verification')
    args = parser.parse_args()
    if args.html:
        html = args.html.read_text(encoding='utf-8')
    else:
        request = Request(PROFILE, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.9'})
        with urlopen(request, timeout=45) as response:
            html = response.read().decode('utf-8')
    papers = json.loads((REPO / '_data/publications.json').read_text(encoding='utf-8'))
    data = build_metrics(html, papers)
    badges = args.output / 'badges'
    badges.mkdir(parents=True, exist_ok=True)
    (args.output / 'metrics.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for key, paper in data['publications'].items():
        badge = {'schemaVersion': 1, 'label': 'citations', 'message': str(paper['citations']) if paper['status'] == 'indexed' else 'pending', 'color': '174d67' if paper['status'] == 'indexed' else '777777', 'namedLogo': 'googlescholar', 'cacheSeconds': 3600}
        (badges / f'{key}.json').write_text(json.dumps(badge) + '\n', encoding='utf-8')
    print(f"Updated {sum(p['status'] == 'indexed' for p in data['publications'].values())}/{len(papers)} selected papers from Google Scholar at {data['updated']}")


if __name__ == '__main__':
    main()
