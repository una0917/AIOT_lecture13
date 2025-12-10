import csv
from pathlib import Path
import math

CSV = Path(__file__).resolve().parent / "movie.csv"
OUT_DIR = Path(__file__).resolve().parent / "site"
OUT_DIR.mkdir(exist_ok=True)


BASE_HTML = '''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>自製電影列表 - Page {page}</title>
  <link rel="stylesheet" href="style.css">
  </head>
<body>
  <div class="container">
    <h1>自製電影列表</h1>
    <div class="grid">
    {cards}
    </div>

    <div class="pagination">
      {pagination}
    </div>
  </div>
</body>
</html>
'''


CARD_HTML = '''<div class="card">
  <img class="poster" src="{image}" alt="{title}">
  <div class="info">
    <h2 class="title">{title}</h2>
    <div class="meta">
      <span class="score">評分: {score}</span>
      <span class="types">類型: {types}</span>
    </div>
    <div class="subinfo">
      <span>發行地區: {region}</span>
      <span>片長: {duration_min}</span>
      <span>上映: {release_date}</span>
    </div>
  </div>
</div>
'''


CSS = '''body{font-family: Arial, "Noto Sans TC", sans-serif;background:#f5f5f5;margin:0;padding:20px}
.container{max-width:1100px;margin:0 auto}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}
.card{background:#fff;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.08);display:flex;overflow:hidden}
.poster{width:180px;height:260px;object-fit:cover}
.info{padding:12px;display:flex;flex-direction:column}
.title{margin:0 0 8px 0;font-size:18px}
.meta{font-size:14px;color:#444;margin-bottom:8px}
.meta span{display:inline-block;margin-right:12px}
.subinfo{font-size:13px;color:#666}
.subinfo span{display:inline-block;margin-right:12px}
.pagination{margin:18px 0;text-align:center}
.pagination a{display:inline-block;padding:8px 12px;margin:0 4px;background:#fff;border-radius:4px;color:#333;text-decoration:none;border:1px solid #e6e6e6}
.pagination a.current{background:#007acc;color:#fff;border-color:#007acc}
@media(max-width:700px){.grid{grid-template-columns:1fr}.poster{width:120px;height:170px}}
'''


def read_csv():
    rows = []
    if not CSV.exists():
        print('movie.csv not found:', CSV)
        return rows
    with CSV.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def make_pagination(page, total_pages):
    parts = []
    for p in range(1, total_pages + 1):
        cls = 'current' if p == page else ''
        parts.append(f'<a class="{cls}" href="page{p}.html">{p}</a>')
    return '\n'.join(parts)


def generate():
    rows = read_csv()
    per_page = 10
    total = len(rows)
    total_pages = max(1, math.ceil(total / per_page))

    for p in range(1, total_pages + 1):
        start = (p - 1) * per_page
        page_rows = rows[start:start + per_page]
        cards = []
        for r in page_rows:
            image = r.get('image', '')
            title = r.get('title', '')
            score = r.get('score', '')
            types = r.get('types', '')
            region = r.get('region', '')
            duration = r.get('duration_min', '')
            release = r.get('release_date', '')
            if duration is None:
                duration = ''
            cards.append(CARD_HTML.format(image=image, title=title, score=score, types=types, region=region, duration_min=duration, release_date=release))

        pagination = make_pagination(p, total_pages)
        html = BASE_HTML.format(page=p, cards='\n'.join(cards), pagination=pagination)
        out = OUT_DIR / f'page{p}.html'
        out.write_text(html, encoding='utf-8')

    # write style
    (OUT_DIR / 'style.css').write_text(CSS, encoding='utf-8')
    # write index as page1
    if total_pages >= 1:
        (OUT_DIR / 'index.html').write_text((OUT_DIR / 'page1.html').read_text(encoding='utf-8'), encoding='utf-8')

    print(f'Generated {total_pages} pages in {OUT_DIR}')


if __name__ == '__main__':
    generate()
