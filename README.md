## 📝 專案名稱：AIOT_lecture13 作業

**專案概覽**
- 📡 CWA：下載中央氣象局（CWA）公開 JSON（F-A0010-001），解析出地點、每日最小/最大溫度與天氣描述，儲存到 `CWA/data.db`（SQLite），並提供 `Streamlit` 應用來檢視與繪圖。
- 🎬 Movie：爬取 `https://ssr1.scrape.center/` 第 1~10 頁電影資料，解析出 `title`, `image`, `score`, `types`, `region`, `duration_min`, `release_date`，輸出 `movie/movie.csv`，並產生靜態分頁網站於 `movie/site/`（每頁 10 筆）。

**📂 專案結構（重點）**
- `CWA/`
  - `cwa_crawler.py`：抓取並解析中央氣象局 JSON 的程式
  - `data.json`：抓到的原始 JSON（若有）
  - `data.db`：SQLite，含 `weather`（摘要）與 `weather_daily`（時間序列）表
  - `streamlit_app.py`：本地啟動的 Streamlit 應用程式
- `movie/`
  - `movie_crawler.py`：爬取電影資訊並輸出 `movie.csv`
  - `movie.csv`：爬蟲結果（CSV）
  - `generate_site.py`：把 `movie.csv` 轉成靜態 HTML（`movie/site/`）的腳本
  - `site/`：產生好的靜態頁面（`index.html`, `page1.html`…`page10.html`, `style.css`）
- `README.md`, `RAW_CONVERSATION.md`, `requirements.txt`

**⚙️ 環境需求**
- Python 3.8+（建議 3.10+）
- 建議使用虛擬環境 `venv`。
- 主要套件（請見 `requirements.txt`）：`requests`, `beautifulsoup4`, `pandas`, `streamlit`, `lxml`, `altair`。

**🔧 本機安裝與快速啟動（PowerShell）**
1. 建立與啟用虛擬環境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 執行 CWA 爬蟲並產生資料庫（若尚未有 `data.db`）:

```powershell
python .\CWA\cwa_crawler.py
```

3. 啟動 Streamlit 本地預覽：

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\CWA\streamlit_app.py
```

Streamlit 部署: 🚀 https://aiotlecture13-kdbascelqncqoi4mdqwv8d.streamlit.app/

4. 如果要重新抓電影資料並產生靜態網站：

```powershell
# 重新抓取（可選）
python .\movie\movie_crawler.py
# 用爬到的 movie.csv 產生靜態頁
python .\movie\generate_site.py
# 開啟產生的 index
Start-Process .\movie\site\index.html
```

**📊 CWA 資料庫說明**
- 檔案：`CWA/data.db`（SQLite 格式）
- 主要表格：
  - `weather`：每個地點的摘要（如今日/未來 X 日的 min/max）
  - `weather_daily`：時間序列，欄位包含 `locationName`, `date`, `min_temp`, `max_temp`, `weather`（視程式解析結果不同欄位名可能不同）

你可以用 SQLite GUI 或指令檢視：
```powershell
# 以 sqlite3 命令行（若安裝）
sqlite3 CWA\data.db
.tables
SELECT * FROM weather_daily LIMIT 20;
```

**🔒 SSL / 安全注意**
- 若抓取 CWA 時遇到 SSL 驗證錯誤，程式目前有 fallback 會用 `verify=False` 重新嘗試下載以利開發與示範，但這會跳過憑證驗證，**不建議生產環境使用**。
- 正確的做法：更新系統的受信任 CA，或在受控環境下提供正確的憑證。

**🎬 Movie 爬蟲與靜態站說明**
- `movie/movie_crawler.py`：
  - 爬取 `https://ssr1.scrape.center/` 的第 1~10 頁
  - 解析欄位：`title`, `image`, `score`, `types`（已規範為以逗號分隔的字串），`region`, `duration_min`, `release_date`
  - 輸出 `movie/movie.csv`（UTF-8 / BOM 或 utf-8-sig 依系統需求）
- `movie/generate_site.py`：把 `movie/movie.csv` 切每 10 筆產生 `movie/site/page{n}.html`（伺服器端已渲染，適合用 `file:///` 開啟）

**最後更新**：2025年12月10日  
