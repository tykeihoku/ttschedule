import streamlit as st
import sqlite3
import pandas as pd
import os
from streamlit_calendar import calendar

# ---------------------------------------------------------
# 0. 設定 & フォルダ確認
# ---------------------------------------------------------
UPLOAD_DIR = "uploaded_pdfs"
DB_FILE = "club_events.db"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ---------------------------------------------------------
# 1. データベース（SQLite）読み込み関数
# ---------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_public_events():
    """公開設定（is_public = 1）の予定のみを取得"""
    conn = get_db_connection()
    query = """
        SELECT target_category, event_date, start_time, end_time, event_type, title, location, leader, participants,
               pdf_guidelines, pdf_singles, pdf_singles_2, pdf_singles_3, pdf_doubles, pdf_team,
               url_form, url_form_boy, url_form_girl, url_doc, url_absent, url_sheet
        FROM events 
        WHERE is_public = 1 
        ORDER BY event_date ASC, start_time ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ---------------------------------------------------------
# 2. カレンダーデータ変換 & UI表示関数
# ---------------------------------------------------------
def prepare_calendar_events(df):
    calendar_events = []
    for _, row in df.iterrows():
        s_time = row["start_time"] if pd.notna(row["start_time"]) and row["start_time"] else "00:00"
        e_time = row["end_time"] if pd.notna(row["end_time"]) and row["end_time"] else "23:59"
        
        start_str = f"{row['event_date']}T{s_time}:00"
        end_str = f"{row['event_date']}T{e_time}:00"
        time_display = f"{s_time}〜{e_time}"
        target_cat = row.get("target_category", "合同")

        display_title = f"[{target_cat}] {row['title']}"

        event_dict = {
            "title": display_title,
            "start": start_str,
            "end": end_str,
            "allDay": False,
            "backgroundColor": "#198754",
            "borderColor": "#198754",
            "extendedProps": {
                "target_category": target_cat,
                "event_type": row.get("event_type", "予定"),
                "time_display": time_display,
                "location": row["location"] or "未定",
                "leader": row.get("leader", "") or "未定",
                "participants": row.get("participants", "") or "全グループ/未指定",
                "pdf_guidelines": row.get("pdf_guidelines", ""),
                "pdf_singles": row.get("pdf_singles", ""),
                "pdf_singles_2": row.get("pdf_singles_2", ""),
                "pdf_singles_3": row.get("pdf_singles_3", ""),
                "pdf_doubles": row.get("pdf_doubles", ""),
                "pdf_team": row.get("pdf_team", ""),
                "url_form_boy": row.get("url_form_boy", "") or row.get("url_form", ""),
                "url_form_girl": row.get("url_form_girl", ""),
                "url_doc": row.get("url_doc", ""),
                "url_absent": row.get("url_absent", ""),
                "url_sheet": row.get("url_sheet", "")
            }
        }
        calendar_events.append(event_dict)
    return calendar_events

CALENDAR_OPTIONS = {
    "editable": False,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next",
        "center": "title",
        "right": "today dayGridMonth,listMonth"
    },
    "initialView": "dayGridMonth",
    "locale": "ja"
}

def render_pdf_download_button(label, file_path):
    if file_path and os.path.exists(file_path):
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label=f"📄 {label} DL ({filename})",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.caption(f"・{label}: 添付なし")

def render_external_link(label, url):
    if url and url.strip():
        st.link_button(label, url.strip(), use_container_width=True)

@st.dialog("📌 予定の詳細情報")
def show_event_details(event_info):
    title = event_info.get("title", "")
    start = event_info.get("start", "")[:10]
    props = event_info.get("extendedProps", {})
    
    st.markdown(f"### 【{props.get('target_category')}・{props.get('event_type')}】 {title}")
    st.write(f"📅 **日付:** {start}")
    st.write(f"⏰ **時間:** {props.get('time_display')}")
    st.write(f"🏫 **対象:** {props.get('target_category')}")
    st.write(f"📍 **場所:** {props.get('location')}")
    st.write(f"👨‍🏫 **引率者:** {props.get('leader')}")
    st.write(f"👥 **参加部員:** {props.get('participants')}")
    
    has_links = any([props.get('url_form_boy'), props.get('url_form_girl'), props.get('url_doc'), props.get('url_absent'), props.get('url_sheet')])
    if has_links:
        st.divider()
        st.markdown("#### 🔗 関連リンク・フォーム")
        render_external_link("📋 男子・参加アンケート（Googleフォーム）", props.get("url_form_boy"))
        render_external_link("📋 女子・参加アンケート（Googleフォーム）", props.get("url_form_girl"))
        render_external_link("📝 注意事項（Googleドキュメント）", props.get("url_doc"))
        render_external_link("✋ 欠席連絡（Googleフォーム）", props.get("url_absent"))
        render_external_link("📊 出欠状況（Googleスプレッドシート）", props.get("url_sheet"))

    st.divider()
    st.markdown("#### 📂 添付書類（PDF）")
    render_pdf_download_button("大会要項", props.get("pdf_guidelines"))
    render_pdf_download_button("組み合わせ（シングルス ①）", props.get("pdf_singles"))
    render_pdf_download_button("組み合わせ（シングルス ②）", props.get("pdf_singles_2"))
    render_pdf_download_button("組み合わせ（シングルス ③）", props.get("pdf_singles_3"))
    render_pdf_download_button("組み合わせ（ダブルス）", props.get("pdf_doubles"))
    render_pdf_download_button("組み合わせ（学校対抗）", props.get("pdf_team"))

# ---------------------------------------------------------
# 3. メイン画面
# ---------------------------------------------------------
st.set_page_config(page_title="卓球部 予定表（生徒・保護者用）", page_icon="🏓", layout="wide")
st.title("🏓 卓球部 スケジュール（生徒・保護者用）")

df_public = fetch_public_events()

if not df_public.empty:
    tab1, tab2 = st.tabs(["📆 カレンダー", "📋 一覧リスト"])
    
    with tab1:
        events_data = prepare_calendar_events(df_public)
        cal_result = calendar(events=events_data, options=CALENDAR_OPTIONS, key="student_calendar")
        
        if cal_result and cal_result.get("callback") == "eventClick":
            event_info = cal_result["eventClick"]["event"]
            show_event_details(event_info)
        
    with tab2:
        for _, row in df_public.iterrows():
            target_cat = row.get("target_category", "合同")
            t_str = f"⏰ {row['start_time']}〜{row['end_time']}"
            leader_str = f"\n\n👨‍🏫 引率者: {row['leader']}" if row.get('leader') else ""
            part_str = f"\n\n👥 参加部員: {row['participants']}" if row['participants'] else ""
            st.info(f"**【{row['event_date']}】 [{target_cat}] {row['title']}** ({t_str})\n\n📍 場所: {row['location'] or '未定'}{leader_str}{part_str}")
            
            boy_url = row.get('url_form_boy') or row.get('url_form')
            girl_url = row.get('url_form_girl')
            has_links = any([boy_url, girl_url, row['url_doc'], row['url_absent'], row['url_sheet']])
            if has_links:
                render_external_link("📋 男子・参加アンケート（Googleフォーム）", boy_url)
                render_external_link("📋 女子・参加アンケート（Googleフォーム）", girl_url)
                render_external_link("📝 注意事項（Googleドキュメント）", row['url_doc'])
                render_external_link("✋ 欠席連絡（Googleフォーム）", row['url_absent'])
                render_external_link("📊 出欠状況（Googleスプレッドシート）", row['url_sheet'])

            has_pdf = any([
                row['pdf_guidelines'], row['pdf_singles'], 
                row.get('pdf_singles_2'), row.get('pdf_singles_3'), 
                row['pdf_doubles'], row['pdf_team']
            ])
            if has_pdf:
                with st.expander("📄 添付PDFファイルを確認"):
                    render_pdf_download_button("大会要項", row['pdf_guidelines'])
                    render_pdf_download_button("組み合わせ（シングルス ①）", row['pdf_singles'])
                    render_pdf_download_button("組み合わせ（シングルス ②）", row.get('pdf_singles_2'))
                    render_pdf_download_button("組み合わせ（シングルス ③）", row.get('pdf_singles_3'))
                    render_pdf_download_button("組み合わせ（ダブルス）", row['pdf_doubles'])
                    render_pdf_download_button("組み合わせ（学校対抗）", row['pdf_team'])
else:
    st.write("現在、公開されている予定はありません。")