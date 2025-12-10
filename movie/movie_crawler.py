import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
import re

BASE = "https://ssr1.scrape.center"
OUT_CSV = Path(__file__).resolve().parent / "movie.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
}


def parse_movie_card(card):
    # heuristics to extract title / image / score / categories
    title = None
    img = None
    score = None
    types = None

    # title: try h2, h3, a
    for tag in ("h2", "h3", "a", "h4"):
        t = card.find(tag)
        if t and t.get_text(strip=True):
            title = t.get_text(strip=True)
            break

    # image
    img_tag = card.find("img")
    if img_tag:
        img = img_tag.get("src") or img_tag.get("data-src")

    # score: look for text like '9.0' or class 'score'
    score_tag = card.find(class_="score") or card.find(class_="rating")
    if score_tag:
        score = score_tag.get_text(strip=True)
    else:
        # search for float in text
        txt = card.get_text(separator=" ")
        import re

        m = re.search(r"\b\d\.\d\b", txt)
        if m:
            score = m.group(0)

    # types / categories: try explicit classes then fallback to nearby spans
    cat_tag = card.find(class_="categories") or card.find(class_="tags")
    if cat_tag:
        # split on common separators and join with comma
        raw = cat_tag.get_text(separator=",", strip=True)
        parts = [p.strip() for p in raw.replace("/", ",").replace("|", ",").split(",") if p.strip()]
        types = ", ".join(parts)
    else:
        # fallback: look for span elements with category-like text
        spans = card.find_all("span")
        cats = []
        for s in spans:
            tx = s.get_text(strip=True)
            # filter out purely numeric or very long texts
            if tx and len(tx) <= 40 and not tx.isdigit():
                cats.append(tx)
        if cats:
            # try to pick those that look like categories (no '分钟' or '上映')
            filtered = [c for c in cats if '分钟' not in c and '上映' not in c and not re.match(r"\d{4}-\d{2}-\d{2}", c)]
            if not filtered:
                filtered = cats
            # split items that use separators like '、' or ','
            parts = []
            for c in filtered:
                for sep in ['、', ',', '/']:
                    if sep in c:
                        parts.extend([p.strip() for p in c.split(sep) if p.strip()])
                        break
                else:
                    parts.append(c)
            types = ", ".join(parts[:6])

    return {"title": title or "", "image": img or "", "score": score or "", "types": types or ""}


def scrape_pages(start=1, end=10):
    rows = []
    for i in range(start, end + 1):
        url = f"{BASE}/page/{i}"
        print(f"Fetching {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # find candidate cards: many sites use div with class 'el-card' or 'movie-item'
        cards = soup.find_all("div", class_=lambda c: c and ("movie-item" in c or "el-card" in c or "card" in c))
        if not cards:
            # fallback: find anchors that link to /movie/ or /detail/
            cards = soup.find_all("a", href=True)
        for c in cards:
            info = parse_movie_card(c)
            # additional parsing: find info blocks for region / duration / release date
            # search divs with class containing 'info'
            region = ""
            duration = ""
            release_date = ""
            info_divs = c.find_all("div", class_=lambda cc: cc and "info" in cc)
            for div in info_divs:
                spans = [s.get_text(strip=True) for s in div.find_all("span") if s.get_text(strip=True)]
                # join spans but also inspect each
                for stext in spans:
                    # duration in minutes
                    m = re.search(r"(\d+)\s*分钟|(\d+)\s*分", stext)
                    if m and not duration:
                        duration = m.group(1) or m.group(2) or m.group(0)
                    # release date like YYYY-MM-DD
                    d = re.search(r"(\d{4}-\d{2}-\d{2})", stext)
                    if d and not release_date:
                        release_date = d.group(1)

                    # skip pure separators or duration/date markers
                    if stext.strip() in ['/', '-', '／']:
                        continue
                    if '分钟' in stext or ('分' in stext and re.search(r"\d", stext)):
                        continue
                    if '上映' in stext or re.search(r"\d{4}-\d{2}-\d{2}", stext):
                        continue

                    # otherwise, treat as region candidate (accept single country like '美国')
                    if not region:
                        region = stext.replace(' ', '')

            info['region'] = region
            info['duration_min'] = int(duration) if duration and duration.isdigit() else (int(duration) if duration.isdigit() else (None if duration == '' else None))
            info['release_date'] = release_date

            # filter out empty titles
            if info.get("title"):
                rows.append(info)

        # be polite
        time.sleep(0.5)

    df = pd.DataFrame(rows).drop_duplicates(subset=["title"]).reset_index(drop=True)
    try:
        df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f"Saved {len(df)} movies to {OUT_CSV}")
    except PermissionError:
        tmp = OUT_CSV.with_name(OUT_CSV.stem + "_tmp.csv")
        df.to_csv(tmp, index=False, encoding="utf-8-sig")
        print(f"PermissionError: could not write {OUT_CSV}. Wrote to {tmp} instead.")


if __name__ == "__main__":
    scrape_pages(1, 10)
