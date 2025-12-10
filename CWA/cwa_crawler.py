import os
import json
import sqlite3
import requests
from pathlib import Path

# --- Configuration ---
API_KEY = "CWA-5DD5F9EC-BA27-4BC5-B7C9-3835E19A149E"
OUT_DIR = Path(__file__).resolve().parent
DATA_JSON = OUT_DIR / "data.json"
DB_PATH = OUT_DIR / "data.db"


def download_json(api_key: str, out_path: Path):
    url = (
        "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001"
        f"?Authorization={api_key}&downloadType=WEB&format=JSON"
    )
    print(f"Downloading JSON from: {url}")
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        out_path.write_text(r.text, encoding="utf-8")
        print(f"Saved JSON to {out_path}")
        return json.loads(r.text)
    except requests.exceptions.SSLError as e:
        print("SSL verification failed. Retrying with verify=False (insecure)...")
        # Try again without certificate verification (insecure but may work in restricted envs)
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(url, timeout=20, verify=False)
        r.raise_for_status()
        out_path.write_text(r.text, encoding="utf-8")
        print(f"Saved JSON to {out_path} (downloaded with verify=False)")
        return json.loads(r.text)
    except Exception:
        raise


def extract_locations(data: dict):
    """
    Extract location data from CWA JSON.
    For this dataset (F-A0010-001 agricultural forecast), structure is:
    cwaopendata.resources.resource.data.agrWeatherForecasts.weatherForecasts.location[]
    Each location has weatherElements with MaxT and MinT daily arrays.
    """
    results = []

    try:
        # Navigate to the location list
        cwa = data.get("cwaopendata", {})
        resources = cwa.get("resources", {})
        resource = resources.get("resource", {})
        data_block = resource.get("data", {})
        agr_forecasts = data_block.get("agrWeatherForecasts", {})
        weather_forecasts = agr_forecasts.get("weatherForecasts", {})
        locations = weather_forecasts.get("location", [])

        if not isinstance(locations, list):
            locations = []

        for loc in locations:
            if not isinstance(loc, dict):
                continue

            name = loc.get("locationName", "unknown")
            weather_elem = loc.get("weatherElements", {})

            # Extract MaxT and MinT from daily arrays
            max_t_list = weather_elem.get("MaxT", {}).get("daily", [])
            min_t_list = weather_elem.get("MinT", {}).get("daily", [])

            # Get first day's max and min
            max_t = None
            min_t = None

            if isinstance(max_t_list, list) and len(max_t_list) > 0:
                try:
                    max_t = float(max_t_list[0].get("temperature", 0))
                except (ValueError, TypeError):
                    max_t = None

            if isinstance(min_t_list, list) and len(min_t_list) > 0:
                try:
                    min_t = float(min_t_list[0].get("temperature", 0))
                except (ValueError, TypeError):
                    min_t = None

            # Build description: weather condition from first day
            wx_elem = weather_elem.get("Wx", {}).get("daily", [])
            weather_desc = ""
            if isinstance(wx_elem, list) and len(wx_elem) > 0:
                weather_desc = wx_elem[0].get("weather", "")

            results.append(
                {
                    "location": name,
                    "min_temp": min_t,
                    "max_temp": max_t,
                    "raw": weather_desc,
                }
            )
    except Exception as e:
        print(f"Error parsing locations: {e}")

    return results


def save_to_sqlite(db_path: Path, items: list):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            min_temp REAL,
            max_temp REAL,
            description TEXT
        )
        """
    )
    cur.execute("DELETE FROM weather")
    for it in items:
        cur.execute(
            "INSERT INTO weather (location, min_temp, max_temp, description) VALUES (?,?,?,?)",
            (it.get("location"), it.get("min_temp"), it.get("max_temp"), it.get("raw")),
        )
    conn.commit()
    conn.close()
    print(f"Saved {len(items)} rows into {db_path}")


def extract_daily_records(data: dict):
    """Extract daily records: list of dicts with location, date, min_temp, max_temp, weather"""
    rows = []
    try:
        cwa = data.get("cwaopendata", {})
        resources = cwa.get("resources", {})
        resource = resources.get("resource", {})
        data_block = resource.get("data", {})
        agr_forecasts = data_block.get("agrWeatherForecasts", {})
        weather_forecasts = agr_forecasts.get("weatherForecasts", {})
        locations = weather_forecasts.get("location", [])

        for loc in locations:
            if not isinstance(loc, dict):
                continue
            name = loc.get("locationName", "unknown")
            weather_elem = loc.get("weatherElements", {})

            max_t_list = weather_elem.get("MaxT", {}).get("daily", [])
            min_t_list = weather_elem.get("MinT", {}).get("daily", [])
            wx_list = weather_elem.get("Wx", {}).get("daily", [])

            # Use length of max_t_list as driver; align by index
            n = max(len(max_t_list), len(min_t_list), len(wx_list))
            for i in range(n):
                date = None
                max_t = None
                min_t = None
                wx = ""
                if i < len(max_t_list):
                    date = max_t_list[i].get("dataDate")
                    try:
                        max_t = float(max_t_list[i].get("temperature"))
                    except Exception:
                        max_t = None
                if i < len(min_t_list):
                    if date is None:
                        date = min_t_list[i].get("dataDate")
                    try:
                        min_t = float(min_t_list[i].get("temperature"))
                    except Exception:
                        min_t = None
                if i < len(wx_list):
                    if date is None:
                        date = wx_list[i].get("dataDate")
                    wx = wx_list[i].get("weather", "")

                if date is None:
                    continue

                rows.append({
                    "location": name,
                    "date": date,
                    "min_temp": min_t,
                    "max_temp": max_t,
                    "weather": wx,
                })
    except Exception as e:
        print("Error extracting daily records:", e)

    return rows


def save_daily_to_sqlite(db_path: Path, rows: list):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            date TEXT,
            min_temp REAL,
            max_temp REAL,
            weather TEXT
        )
        """
    )
    # replace data for simplicity
    cur.execute("DELETE FROM weather_daily")
    for r in rows:
        cur.execute(
            "INSERT INTO weather_daily (location, date, min_temp, max_temp, weather) VALUES (?,?,?,?,?)",
            (r.get("location"), r.get("date"), r.get("min_temp"), r.get("max_temp"), r.get("weather")),
        )
    conn.commit()
    conn.close()
    print(f"Saved {len(rows)} daily rows into {db_path}")


def main():
    data = None
    try:
        data = download_json(API_KEY, DATA_JSON)
    except Exception as e:
        print("Download failed:", e)
        if DATA_JSON.exists():
            print("Loading previously saved JSON")
            data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
        else:
            raise

    # summary items (first-day summary)
    items = extract_locations(data)
    print(f"Extracted {len(items)} location summary records")
    save_to_sqlite(DB_PATH, items)

    # daily time series
    daily = extract_daily_records(data)
    print(f"Extracted {len(daily)} daily records")
    save_daily_to_sqlite(DB_PATH, daily)


if __name__ == "__main__":
    main()
