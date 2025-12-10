import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import altair as alt

DB_PATH = Path(__file__).resolve().parent / "data.db"

st.set_page_config(page_title="CWA Weather Viewer", layout="wide")

st.title("中央氣象局 - 天氣時間序列 (SQLite)")

if not DB_PATH.exists():
    st.error(f"資料庫不存在：{DB_PATH}\n請先執行 `cwa_crawler.py` 建立 `data.db`。")
else:
    conn = sqlite3.connect(str(DB_PATH))
    # load daily table
    try:
        df = pd.read_sql_query("SELECT location, date, min_temp, max_temp, weather FROM weather_daily", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()

    st.sidebar.header("過濾條件")
    if df.empty:
        st.warning("資料庫中沒有 `weather_daily` 資料，請先執行爬蟲以產生時間序列資料。")
    else:
        # normalize
        df['date'] = pd.to_datetime(df['date'])

        locations = sorted(df['location'].unique())
        sel = st.sidebar.selectbox("選擇區域", options=["All"] + locations)

        if sel == "All":
            df_sel = df.copy()
        else:
            df_sel = df[df['location'] == sel].copy()

        st.subheader(f"時間序列：{sel}")
        st.dataframe(df_sel.reset_index(drop=True))

        # prepare chart: index by date and display min/max with visible markers
        if not df_sel.empty:
            chart_df = df_sel.set_index('date')[['min_temp', 'max_temp']].sort_index()
            chart_df = chart_df.reset_index().melt(id_vars=['date'], value_vars=['min_temp', 'max_temp'], var_name='type', value_name='temp')

            chart = (
                alt.Chart(chart_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X('date:T', title='日期'),
                    y=alt.Y('temp:Q', title='溫度 (˚C)'),
                    color=alt.Color('type:N', title='類別'),
                    tooltip=[alt.Tooltip('date:T', title='日期'), alt.Tooltip('type:N', title='類別'), alt.Tooltip('temp:Q', title='溫度')],
                )
                .properties(height=420)
            )

            st.altair_chart(chart, use_container_width=True)
