import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import date, datetime, time
from streamlit_calendar import calendar

# ---------------------------------------------------------
# 0. 設定・フォルダ作成＆パスワード定義
# ---------------------------------------------------------
TEACHER_PASSWORD = "tktt"
UPLOAD_DIR = "uploaded_pdfs"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ---------------------------------------------------------
# 1. データベース（SQLite）ヘルパー関数
# ---------------------------------------------------------
DB_FILE = "club_events.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_category TEXT DEFAULT '合同',
            event_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT '通常練習',
            title TEXT NOT NULL,
            location TEXT,
            leader TEXT DEFAULT '',
            is_public INTEGER NOT NULL DEFAULT 1,
            status_application TEXT DEFAULT '不要',
            status_payment TEXT DEFAULT '不要',
            status_trip TEXT DEFAULT '不要',
            status_holiday_notice TEXT DEFAULT '不要',
            status_roster TEXT DEFAULT '不要',
            status_delegation TEXT DEFAULT '不要',
            participants TEXT DEFAULT '',
            pdf_guidelines TEXT DEFAULT '',
            pdf_singles TEXT DEFAULT '',
            pdf_singles_2 TEXT DEFAULT '',
            pdf_singles_3 TEXT DEFAULT '',
            pdf_doubles TEXT DEFAULT '',
            pdf_team TEXT DEFAULT '',
            url_form TEXT DEFAULT '',
            url_form_boy TEXT DEFAULT '',
            url_form_girl TEXT DEFAULT '',
            url_doc TEXT DEFAULT '',
            url_absent TEXT DEFAULT '',
            url_sheet TEXT DEFAULT ''
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_type TEXT DEFAULT '高校',
            grade TEXT NOT NULL,
            class_num TEXT DEFAULT '',
            attendance_num INTEGER DEFAULT 0,
            name TEXT NOT NULL,
            position TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT DEFAULT '顧問',
            note TEXT DEFAULT ''
        )
    """)
    
    cursor.execute("PRAGMA table_info(events)")
    event_cols = [col[1] for col in cursor.fetchall()]
    new_cols = {
        "target_category": "TEXT DEFAULT '合同'",
        "leader": "TEXT DEFAULT ''",
        "participants": "TEXT DEFAULT ''",
        "pdf_guidelines": "TEXT DEFAULT ''",
        "pdf_singles": "TEXT DEFAULT ''",
        "pdf_singles_2": "TEXT DEFAULT ''",
        "pdf_singles_3": "TEXT DEFAULT ''",
        "pdf_doubles": "TEXT DEFAULT ''",
        "pdf_team": "TEXT DEFAULT ''",
        "url_form": "TEXT DEFAULT ''",
        "url_form_boy": "TEXT DEFAULT ''",
        "url_form_girl": "TEXT DEFAULT ''",
        "url_doc": "TEXT DEFAULT ''",
        "url_absent": "TEXT DEFAULT ''",
        "url_sheet": "TEXT DEFAULT ''"
    }
    for col_name, col_type in new_cols.items():
        if col_name not in event_cols:
            cursor.execute(f"ALTER TABLE events ADD COLUMN {col_name} {col_type}")

    cursor.execute("PRAGMA table_info(members)")
    member_cols = [col[1] for col in cursor.fetchall()]
    if "school_type" not in member_cols:
        cursor.execute("ALTER TABLE members ADD COLUMN school_type TEXT DEFAULT '高校'")
    if "class_num" not in member_cols:
        cursor.execute("ALTER TABLE members ADD COLUMN class_num TEXT DEFAULT ''")
    if "attendance_num" not in member_cols:
        cursor.execute("ALTER TABLE members ADD COLUMN attendance_num INTEGER DEFAULT 0")
            
    conn.commit()
    conn.close()

def save_uploaded_file(uploaded_file, prefix):
    if uploaded_file is None:
        return ""
    file_path = os.path.join(UPLOAD_DIR, f"{prefix}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# --- 部員 ---
def add_member(school_type, grade, class_num, attendance_num, name, position):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO members (school_type, grade, class_num, attendance_num, name, position) VALUES (?, ?, ?, ?, ?, ?)",
        (school_type, grade, class_num, attendance_num, name, position)
    )
    conn.commit()
    conn.close()

def fetch_members():
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM members ORDER BY school_type DESC, grade ASC, class_num ASC, attendance_num ASC, name ASC",
        conn
    )
    conn.close()
    return df

def delete_member(member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()

# --- 教員 ---
def add_teacher(name, role, note):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teachers (name, role, note) VALUES (?, ?, ?)",
        (name, role, note)
    )
    conn.commit()
    conn.close()

def fetch_teachers():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM teachers ORDER BY id ASC", conn)
    conn.close()
    return df

def delete_teacher(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
    conn.commit()
    conn.close()

# --- 予定 ---
def add_event(target_category, event_date, start_time, end_time, event_type, title, location, leader, is_public,
              status_application, status_payment, status_trip, status_holiday_notice, status_roster, status_delegation,
              participants_str, pdf_guidelines, pdf_singles, pdf_singles_2, pdf_singles_3, pdf_doubles, pdf_team,
              url_form_boy, url_form_girl, url_doc, url_absent, url_sheet):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (
            target_category, event_date, start_time, end_time, event_type, title, location, leader, is_public,
            status_application, status_payment, status_trip, status_holiday_notice, status_roster, status_delegation,
            participants, pdf_guidelines, pdf_singles, pdf_singles_2, pdf_singles_3, pdf_doubles, pdf_team,
            url_form_boy, url_form_girl, url_doc, url_absent, url_sheet
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        target_category, str(event_date), str(start_time), str(end_time), event_type, title, location, leader,
        1 if is_public else 0, status_application, status_payment, status_trip,
        status_holiday_notice, status_roster, status_delegation, participants_str,
        pdf_guidelines, pdf_singles, pdf_singles_2, pdf_singles_3, pdf_doubles, pdf_team,
        url_form_boy, url_form_girl, url_doc, url_absent, url_sheet
    ))
    conn.commit()
    conn.close()

def fetch_events(is_teacher=False):
    conn = get_db_connection()
    if is_teacher:
        query = "SELECT * FROM events ORDER BY event_date ASC, start_time ASC"
        df = pd.read_sql_query(query, conn)
    else:
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

def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# 2. カレンダー形式用データ変換関数 & 詳細表示ダイアログ
# ---------------------------------------------------------
def prepare_calendar_events(df, is_teacher=False):
    calendar_events = []
    for _, row in df.iterrows():
        s_time = row["start_time"] if pd.notna(row["start_time"]) and row["start_time"] else "00:00"
        e_time = row["end_time"] if pd.notna(row["end_time"]) and row["end_time"] else "23:59"
        
        start_str = f"{row['event_date']}T{s_time}:00"
        end_str = f"{row['event_date']}T{e_time}:00"
        time_display = f"{s_time}〜{e_time}"
        target_cat = row.get("target_category", "合同")

        has_unapplied = False
        if is_teacher and row.get("event_type") in ["大会", "練習試合"]:
            statuses = [
                row.get("status_application"),
                row.get("status_payment"),
                row.get("status_trip"),
                row.get("status_holiday_notice"),
                row.get("status_roster"),
                row.get("status_delegation")
            ]
            if "未申請" in statuses:
                has_unapplied = True

        display_title = f"[{target_cat}] {row['title']}"
        if has_unapplied:
            display_title = f"⚠️ {display_title}"

        event_dict = {
            "title": display_title,
            "start": start_str,
            "end": end_str,
            "allDay": False,
            "extendedProps": {
                "target_category": target_cat,
                "event_type": row.get("event_type", "予定"),
                "time_display": time_display,
                "location": row["location"] or "未定",
                "leader": row.get("leader", "") or "未定",
                "participants": row.get("participants", "") or "設定なし",
                "is_public": "公開" if row.get("is_public", 1) == 1 else "非公開",
                "status_application": row.get("status_application", "不要"),
                "status_payment": row.get("status_payment", "不要"),
                "status_trip": row.get("status_trip", "不要"),
                "status_holiday_notice": row.get("status_holiday_notice", "不要"),
                "status_roster": row.get("status_roster", "不要"),
                "status_delegation": row.get("status_delegation", "不要"),
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
        
        if is_teacher:
            if row.get("is_public") == 0:
                event_dict["backgroundColor"] = "#6c757d"
                event_dict["borderColor"] = "#6c757d"
            elif has_unapplied:
                event_dict["backgroundColor"] = "#dc3545"
                event_dict["borderColor"] = "#dc3545"
            elif row.get("event_type") in ["大会", "練習試合"]:
                event_dict["backgroundColor"] = "#0d6efd"
                event_dict["borderColor"] = "#0d6efd"
            else:
                event_dict["backgroundColor"] = "#0dcaf0"
                event_dict["borderColor"] = "#0dcaf0"
        else:
            event_dict["backgroundColor"] = "#198754"
            event_dict["borderColor"] = "#198754"
            
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
def show_event_details(event_info, is_teacher=False):
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
    
    if is_teacher:
        st.divider()
        st.markdown("#### 💼 事務・申請管理ステータス")
        if props.get("event_type") in ["大会", "練習試合"]:
            st.write(f"・**申込:** {props.get('status_application')} / **支払い:** {props.get('status_payment')}")
            st.write(f"・**出張申請:** {props.get('status_trip')} / **休日活動届:** {props.get('status_holiday_notice')}")
            st.write(f"・**部員名簿提出:** {props.get('status_roster')} / **委任状:** {props.get('status_delegation')}")
        else:
            st.caption("※事務管理項目はありません。")
            
        st.write(f"🔒 **公開状態:** {props.get('is_public')}")

def parse_time_str(time_str, default_time):
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except (ValueError, TypeError):
        return default_time

# ---------------------------------------------------------
# 3. アプリ初期設定 & UI構築
# ---------------------------------------------------------
init_db()

st.set_page_config(page_title="卓球部 予定＆事務管理", page_icon="🏓", layout="wide")
st.title("🏓 卓球部 スケジュール管理（教員用）")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.subheader("🔒 教員モード・ログイン")
    with st.form("login_form"):
        password_input = st.text_input("パスワード", type="password")
        login_button = st.form_submit_button("ログイン")
        if login_button:
            if password_input == TEACHER_PASSWORD:
                st.session_state.authenticated = True
                st.success("認証に成功しました！")
                st.rerun()
            else:
                st.error("パスワードが正しくありません。")

else:
    if st.sidebar.button("🚪 ログアウト"):
        st.session_state.authenticated = False
        st.rerun()

    tab_schedule, tab_teachers, tab_members = st.tabs(["📅 スケジュール & 事務管理", "👨‍🏫 教員名簿", "👥 部員名簿"])

    # ---------------------------------------------------------
    # タブ 1: スケジュール & 事務管理
    # ---------------------------------------------------------
    with tab_schedule:
        df_all = fetch_events(is_teacher=True)
        df_members = fetch_members()
        df_teachers = fetch_teachers()
        
        # 全部員リスト
        member_options_all = []
        member_options_hs = []
        member_options_ms = []
        if not df_members.empty:
            for _, r in df_members.iterrows():
                stype = r.get('school_type', '高校')
                cls_info = f" {r['class_num']}" if r['class_num'] else ""
                att_info = f" {r['attendance_num']}番" if r['attendance_num'] > 0 else ""
                item_str = f"[{stype}]{r['grade']}{cls_info}{att_info} {r['name']}"
                
                member_options_all.append(item_str)
                if stype == "高校":
                    member_options_hs.append(item_str)
                elif stype == "中学":
                    member_options_ms.append(item_str)

        # 教員リスト（引率者用）
        teacher_options = []
        if not df_teachers.empty:
            for _, r in df_teachers.iterrows():
                role_str = f"（{r['role']}）" if r['role'] else ""
                teacher_options.append(f"{r['name']} 先生{role_str}")

        if not df_all.empty:
            with st.expander("📆 カレンダーを表示（クリックで詳細確認）", expanded=True):
                st.caption("🔴 未申請あり / 🔵 事務完了大会 / 🩵 通常練習 / 🔒 非公開")
                events_teacher_data = prepare_calendar_events(df_all, is_teacher=True)
                cal_teacher_result = calendar(events=events_teacher_data, options=CALENDAR_OPTIONS, key="teacher_calendar")
                
                if cal_teacher_result and cal_teacher_result.get("callback") == "eventClick":
                    event_info = cal_teacher_result["eventClick"]["event"]
                    show_event_details(event_info, is_teacher=True)

        st.divider()
        
        sub_tab_add, sub_tab_list = st.tabs(["➕ 新規予定・事務登録", "📋 登録一覧・削除"])
        
        with sub_tab_add:
            copy_template = None
            if not df_all.empty:
                st.markdown("##### 📋 過去の予定からコピーして入力")
                copy_options = ["（新規作成・コピーしない）"] + [
                    f"【{row['event_date']}】[{row.get('target_category', '合同')}] {row['title']}（{row['event_type']}）"
                    for _, row in df_all.iterrows()
                ]
                selected_copy = st.selectbox("複製元にする予定を選択", copy_options, key="event_copy_selectbox")
                
                if selected_copy != "（新規作成・コピーしない）":
                    selected_idx = copy_options.index(selected_copy) - 1
                    copy_template = df_all.iloc[selected_idx]
                    st.info(f"💡 「{copy_template['title']}」の内容を下のフォームに呼び出しました。日付などを修正して保存してください。")

            default_target = copy_template.get("target_category", "合同") if copy_template is not None else "合同"
            default_type = copy_template["event_type"] if copy_template is not None else "通常練習"
            default_title = copy_template["title"] if copy_template is not None else ""
            default_location = copy_template["location"] if copy_template is not None else ""
            default_leader = copy_template.get("leader", "") if copy_template is not None else ""
            default_start_time = parse_time_str(copy_template["start_time"], time(9, 0)) if copy_template is not None else time(9, 0)
            default_end_time = parse_time_str(copy_template["end_time"], time(12, 0)) if copy_template is not None else time(12, 0)
            default_is_public = bool(copy_template["is_public"]) if copy_template is not None else True
            
            default_url_form_boy = ""
            if copy_template is not None:
                default_url_form_boy = copy_template.get("url_form_boy") or copy_template.get("url_form") or ""
            default_url_form_girl = copy_template.get("url_form_girl", "") if copy_template is not None else ""
            default_url_doc = copy_template.get("url_doc", "") if copy_template is not None else ""
            default_url_absent = copy_template.get("url_absent", "") if copy_template is not None else ""
            default_url_sheet = copy_template.get("url_sheet", "") if copy_template is not None else ""

            cat_list = ["高校", "中学", "合同", "その他"]
            cat_index = cat_list.index(default_target) if default_target in cat_list else 2

            event_types_list = ["大会", "練習試合", "通常練習", "ミーティング", "その他"]
            type_index = event_types_list.index(default_type) if default_type in event_types_list else 0

            # 引率者のプルダウン選択肢（教員優先、無ければ部員）
            leader_select_list = teacher_options if teacher_options else member_options_all
            leader_options = ["未設定"] + leader_select_list
            leader_index = 0
            if default_leader in leader_options:
                leader_index = leader_options.index(default_leader)

            status_opts = ["未申請", "申請済", "不要"]
            def get_status_idx(val):
                return status_opts.index(val) if val in status_opts else 2

            with st.form("add_event_form", clear_on_submit=True):
                col_cat, col_type = st.columns(2)
                with col_cat:
                    target_category = st.selectbox("対象（区分）", cat_list, index=cat_index)
                with col_type:
                    event_type = st.selectbox("予定の種類", event_types_list, index=type_index)

                event_date = st.date_input("日付", date.today())
                
                c_start, c_end = st.columns(2)
                with c_start:
                    start_t = st.time_input("開始時間", value=default_start_time)
                with c_end:
                    end_t = st.time_input("終了時間", value=default_end_time)
                
                title = st.text_input("予定タイトル", value=default_title)
                location = st.text_input("場所", value=default_location)
                
                selected_leader = st.selectbox("👨‍🏫 引率者", options=leader_options, index=leader_index)
                if not teacher_options:
                    st.caption("※教員名簿が未登録のため、部員リストを表示しています。「👨‍🏫 教員名簿」タブから教員を追加できます。")

                if target_category == "高校":
                    active_member_opts = member_options_hs if member_options_hs else member_options_all
                elif target_category == "中学":
                    active_member_opts = member_options_ms if member_options_ms else member_options_all
                else:
                    active_member_opts = member_options_all

                default_participants = active_member_opts
                if copy_template is not None and copy_template["participants"]:
                    template_parts = [p.strip() for p in copy_template["participants"].split(",")]
                    default_participants = [m for m in active_member_opts if m in template_parts]

                selected_members = []
                if active_member_opts:
                    selected_members = st.multiselect("対象部員", options=active_member_opts, default=default_participants)

                st.markdown("##### 🔗 Googleフォーム / ドキュメント / スプレッドシート リンク設定")
                col_fb, col_fg = st.columns(2)
                with col_fb:
                    url_form_boy = st.text_input("📋 男子・参加アンケート (Googleフォーム)", value=default_url_form_boy, placeholder="https://forms.gle/...")
                with col_fg:
                    url_form_girl = st.text_input("📋 女子・参加アンケート (Googleフォーム)", value=default_url_form_girl, placeholder="https://forms.gle/...")

                url_doc = st.text_input("📝 注意事項 (Googleドキュメント URL)", value=default_url_doc, placeholder="https://docs.google.com/document/d/...")
                url_absent = st.text_input("✋ 欠席連絡 (Googleフォーム URL)", value=default_url_absent, placeholder="https://forms.gle/...")
                url_sheet = st.text_input("📊 出欠状況 (Googleスプレッドシート URL)", value=default_url_sheet, placeholder="https://docs.google.com/spreadsheets/d/...")

                st.markdown("##### 📄 PDF添付")
                pdf_guidelines_file = st.file_uploader("大会要項 (PDF)", type=["pdf"])
                
                st.caption("シングルスの組み合わせ（最大3ファイルまでアップロード可）")
                pdf_singles_file = st.file_uploader("組み合わせ：シングルス ① (PDF)", type=["pdf"])
                pdf_singles_file_2 = st.file_uploader("組み合わせ：シングルス ② (PDF)", type=["pdf"])
                pdf_singles_file_3 = st.file_uploader("組み合わせ：シングルス ③ (PDF)", type=["pdf"])
                
                pdf_doubles_file = st.file_uploader("組み合わせ：ダブルス (PDF)", type=["pdf"])
                pdf_team_file = st.file_uploader("組み合わせ：学校対抗 (PDF)", type=["pdf"])

                is_public = st.checkbox("生徒・保護者に公開する", value=default_is_public)
                
                st.markdown("##### 💼 事務管理（大会・練習試合用）")
                
                app_idx = get_status_idx(copy_template["status_application"]) if copy_template is not None else 0
                pay_idx = get_status_idx(copy_template["status_payment"]) if copy_template is not None else 0
                trip_idx = get_status_idx(copy_template["status_trip"]) if copy_template is not None else 0
                hol_idx = get_status_idx(copy_template["status_holiday_notice"]) if copy_template is not None else 0
                ros_idx = get_status_idx(copy_template["status_roster"]) if copy_template is not None else 0
                del_idx = get_status_idx(copy_template["status_delegation"]) if copy_template is not None else 0

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    status_app = st.selectbox("申込", status_opts, index=app_idx)
                    status_pay = st.selectbox("支払い", status_opts, index=pay_idx)
                    status_trip = st.selectbox("出張申請", status_opts, index=trip_idx)
                with col_m2:
                    status_holiday = st.selectbox("休日活動届", status_opts, index=hol_idx)
                    status_roster = st.selectbox("部員名簿", status_opts, index=ros_idx)
                    status_delegation = st.selectbox("委任状", status_opts, index=del_idx)

                submitted = st.form_submit_button("保存する", use_container_width=True)
                if submitted:
                    if title.strip() == "":
                        st.error("予定タイトルを入力してください。")
                    else:
                        s_time_str = start_t.strftime("%H:%M")
                        e_time_str = end_t.strftime("%H:%M")
                        if event_type not in ["大会", "練習試合"]:
                            status_app = status_pay = status_trip = status_holiday = status_roster = status_delegation = "不要"
                        participants_str = ", ".join(selected_members) if selected_members else "全員/未指定"
                        leader_str = "" if selected_leader == "未設定" else selected_leader
                        
                        timestamp_prefix = date.today().strftime("%Y%m%d")
                        path_guidelines = save_uploaded_file(pdf_guidelines_file, f"{timestamp_prefix}_guidelines")
                        path_singles = save_uploaded_file(pdf_singles_file, f"{timestamp_prefix}_singles")
                        path_singles_2 = save_uploaded_file(pdf_singles_file_2, f"{timestamp_prefix}_singles2")
                        path_singles_3 = save_uploaded_file(pdf_singles_file_3, f"{timestamp_prefix}_singles3")
                        path_doubles = save_uploaded_file(pdf_doubles_file, f"{timestamp_prefix}_doubles")
                        path_team = save_uploaded_file(pdf_team_file, f"{timestamp_prefix}_team")

                        add_event(
                            target_category, event_date, s_time_str, e_time_str, event_type, title, location, leader_str, is_public,
                            status_app, status_pay, status_trip, status_holiday, status_roster, status_delegation,
                            participants_str, path_guidelines, path_singles, path_singles_2, path_singles_3, path_doubles, path_team,
                            url_form_boy, url_form_girl, url_doc, url_absent, url_sheet
                        )
                        st.success("✅ 登録しました！")
                        st.rerun()

        with sub_tab_list:
            if not df_all.empty:
                df_display = df_all.copy()
                df_display["時間"] = df_display.apply(lambda r: f"{r['start_time']}〜{r['end_time']}", axis=1)
                df_display["公開"] = df_display["is_public"].apply(lambda x: "🟢" if x == 1 else "🔒")
                
                show_cols = ["id", "target_category", "event_date", "時間", "event_type", "title", "leader", "公開"]
                df_render = df_display[show_cols]
                df_render.columns = ["ID", "区分", "日付", "時間", "種別", "タイトル", "引率者", "公開"]
                
                st.dataframe(df_render, use_container_width=True, hide_index=True)
                
                with st.expander("🗑️ 予定の削除"):
                    event_ids = df_all["id"].tolist()
                    selected_id = st.selectbox("削除対象のID", event_ids)
                    if st.button("削除実行", use_container_width=True):
                        delete_event(selected_id)
                        st.warning("削除しました。")
                        st.rerun()
            else:
                st.write("予定なし")

    # ---------------------------------------------------------
    # タブ 2: 教員名簿の登録・管理
    # ---------------------------------------------------------
    with tab_teachers:
        sub_t_add, sub_t_list = st.tabs(["➕ 教員の追加", "📋 教員名簿"])
        
        with sub_t_add:
            with st.form("add_teacher_form", clear_on_submit=True):
                t_name = st.text_input("教員氏名 (例: 山田 太郎)")
                t_role = st.selectbox("役職・役割", ["主顧問", "副顧問", "外部指導員", "部活動指導員", "その他"])
                t_note = st.text_input("備考 (任意: 担当教科など)")
                
                t_submitted = st.form_submit_button("教員を追加", use_container_width=True)
                if t_submitted:
                    if t_name.strip() == "":
                        st.error("氏名を入力してください。")
                    else:
                        add_teacher(t_name.strip(), t_role, t_note.strip())
                        st.success(f"✅ {t_name} 先生を登録しました！")
                        st.rerun()
                        
        with sub_t_list:
            df_t = fetch_teachers()
            if not df_t.empty:
                df_t_display = df_t[["id", "name", "role", "note"]].copy()
                df_t_display.columns = ["ID", "氏名", "役職", "備考"]
                st.dataframe(df_t_display, use_container_width=True, hide_index=True)
                
                with st.expander("🗑️ 教員の削除"):
                    t_ids = df_t["id"].tolist()
                    sel_t_id = st.selectbox("削除対象のID", t_ids, key="del_teacher_id")
                    if st.button("教員を削除", use_container_width=True):
                        delete_teacher(sel_t_id)
                        st.warning("削除しました。")
                        st.rerun()
            else:
                st.info("教員が登録されていません。上の「➕ 教員の追加」から登録してください。")

    # ---------------------------------------------------------
    # タブ 3: 部員名簿の登録・管理
    # ---------------------------------------------------------
    with tab_members:
        sub_m_add, sub_m_list = st.tabs(["➕ 部員の追加", "📋 部員名簿・データ出力"])
        
        with sub_m_add:
            with st.form("add_member_form", clear_on_submit=True):
                col_stype, col_grd = st.columns(2)
                with col_stype:
                    m_school_type = st.selectbox("区分", ["高校", "中学", "その他"])
                with col_grd:
                    if m_school_type == "高校":
                        m_grade = st.selectbox("学年", ["高1", "高2", "高3"])
                    elif m_school_type == "中学":
                        m_grade = st.selectbox("学年", ["中1", "中2", "中3"])
                    else:
                        m_grade = st.selectbox("区分", ["マネージャー", "顧問", "コーチ", "その他"])

                col_cls, col_att = st.columns(2)
                class_options = ["なし"] + [f"{i}組" for i in range(1, 11)]
                with col_cls:
                    m_class_sel = st.selectbox("クラス", class_options)
                
                att_options = ["なし"] + [f"{i}番" for i in range(1, 46)]
                with col_att:
                    m_att_sel = st.selectbox("出席番号", att_options)

                m_name = st.text_input("氏名")
                m_pos = st.text_input("戦型・役割")
                
                m_submitted = st.form_submit_button("名簿に追加", use_container_width=True)
                if m_submitted:
                    if m_name.strip() == "":
                        st.error("氏名を入力してください。")
                    else:
                        class_val = "" if m_class_sel == "なし" else m_class_sel
                        att_val = 0 if m_att_sel == "なし" else int(m_att_sel.replace("番", ""))
                        
                        add_member(m_school_type, m_grade, class_val, att_val, m_name.strip(), m_pos.strip())
                        st.success(f"✅ {m_name} さんを登録しました！")
                        st.rerun()
                        
        with sub_m_list:
            df_m = fetch_members()
            if not df_m.empty:
                df_m_display = df_m[["id", "school_type", "grade", "class_num", "attendance_num", "name", "position"]].copy()
                df_m_display["attendance_num"] = df_m_display["attendance_num"].apply(lambda x: f"{x}番" if x > 0 else "")
                df_m_display.columns = ["ID", "区分", "学年", "組", "番", "氏名", "戦型"]
                st.dataframe(df_m_display, use_container_width=True, hide_index=True)
                
                st.divider()
                st.markdown("##### 📋 Excelコピー / CSV出力")
                target_group = st.selectbox(
                    "対象絞り込み", 
                    ["全員", "高校生のみ", "中学生のみ", "高1のみ", "高2のみ", "高3のみ"],
                    key="export_filter"
                )
                export_mode = st.selectbox(
                    "形式",
                    ["名前のみ（縦一列）", "詳細データ（タブ区切り）"]
                )
                
                if target_group == "全員":
                    df_target = df_m.copy()
                elif target_group == "高校生のみ":
                    df_target = df_m[df_m["school_type"] == "高校"].copy()
                elif target_group == "中学生のみ":
                    df_target = df_m[df_m["school_type"] == "中学"].copy()
                else:
                    filter_grd = target_group.replace("のみ", "")
                    df_target = df_m[df_m["grade"] == filter_grd].copy()
                
                if export_mode == "名前のみ（縦一列）":
                    text_for_excel = "\n".join(df_target["name"].tolist())
                else:
                    lines = [f"{r['school_type']}\t{r['grade']}\t{r['class_num']}\t{r['attendance_num']}番\t{r['name']}" for _, r in df_target.iterrows()]
                    text_for_excel = "\n".join(lines)
                
                st.text_area("コピー用テキスト", value=text_for_excel, height=120)

                with st.expander("🗑️ 部員削除"):
                    m_ids = df_m["id"].tolist()
                    sel_m_id = st.selectbox("削除対象のID", m_ids, key="del_member_id")
                    if st.button("部員を削除", use_container_width=True):
                        delete_member(sel_m_id)
                        st.warning("削除しました。")
                        st.rerun()
            else:
                st.info("部員が登録されていません。")