# 課堂作業：資料爬蟲 + SQLite + Streamlit

專案結構（在 `AIOT_lecture13` 下）:

- `CWA/`
  - `cwa_crawler.py` : 下載中央氣象局 JSON、解析並寫入 `data.db`
  - `streamlit_app.py` : 讀取 `data.db` 並以 Streamlit 顯示
  - `data.db` : 執行爬蟲後會產生（不會加入版本控制）
- `movie/`
  - `movie_crawler.py` : 爬取 `ssr1.scrape.center` page/1..10，產生 `movie.csv`

依賴：請先建立虛擬環境並安裝 `requirements.txt`。

快速開始（PowerShell）:

```powershell
cd C:\Users\Una\AIOT\AIOT_lecture13
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 執行中央氣象局爬蟲，會建立 CWA/data.json 與 CWA/data.db
python .\CWA\cwa_crawler.py

# 執行電影爬蟲，會建立 movie/movie.csv
python .\movie\movie_crawler.py

# 執行 Streamlit (會打開本地網頁，請自行截圖 Streamlit 介面)
streamlit run .\CWA\streamlit_app.py
```

備註：
- `cwa_crawler.py` 包含容錯和多種解析嘗試，若 JSON 結構有變動，會把 raw JSON 片段存進 `description` 欄位。
- 如果需要，我可以幫你執行以上命令並把 `data.db`、`movie/movie.csv` 產生於專案資料夾。
