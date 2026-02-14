import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
from datetime import datetime, date, time, timedelta
import jpholiday

st.set_page_config(page_title="シフト入力", layout="wide")

ADMIN_PASSWORD = "admin123"  # 管理者パスワード

# -------------------------
# セッション管理
# -------------------------
if "username" not in st.session_state:
    st.session_state.username = None

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

# -------------------------
# ログイン画面
# -------------------------
if st.session_state.username is None:
    st.title("シフト入力アプリ")

    name = st.text_input("名前を入力してください")
    admin_pw = st.text_input("管理者パスワード（一般ユーザーは空欄でOK）", type="password")

    if st.button("ログイン"):
        if name.strip() == "":
            st.warning("名前を入力してください")
        else:
            st.session_state.username = name

            # 管理者判定
            if admin_pw == ADMIN_PASSWORD:
                st.session_state.is_admin = True
            else:
                st.session_state.is_admin = False

    st.stop()

# -------------------------
# 管理者画面
# -------------------------
if st.session_state.is_admin:
    st.title("管理者画面")
    st.write(f"管理者としてログイン中：**{st.session_state.username}** さん")

    tabs = st.tabs([
        "① シフト一覧",
        "② 編集",
        "③ 削除",
        "④ CSV ダウンロード",
        "⑤ カレンダー表示",
        "⑥ 日別人数カウント",
        "⑦ 月間勤務時間集計",
        "⑧ 時間帯別人数集計",
        "⑨ シフトデータ初期化"
    ])

    # -------------------------
    # ① シフト一覧
    # -------------------------
    with tabs[0]:
        st.subheader("① シフト一覧（検索・並び替え）")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None:
            name_filter = st.text_input("名前で検索（部分一致）")
            date_filter = st.date_input("日付で検索（任意）", value=None)

            filtered = df.copy()

            if name_filter:
                filtered = filtered[filtered["name"].str.contains(name_filter)]

            if date_filter:
                filtered = filtered[filtered["date"] == date_filter.strftime("%Y-%m-%d")]

            sort_col = st.selectbox("並び替え列", ["date", "name", "start", "end"])
            sort_asc = st.checkbox("昇順", value=True)

            filtered = filtered.sort_values(sort_col, ascending=sort_asc)

            st.dataframe(filtered, use_container_width=True)

    # -------------------------
    # ② 編集
    # -------------------------
    with tabs[1]:
        st.subheader("② シフト編集")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None and len(df) > 0:
            row_index = st.number_input("行番号（0〜）", min_value=0, max_value=len(df)-1, step=1)
            target = df.iloc[row_index]

            st.write("現在のデータ：", target)

            new_name = st.text_input("名前", value=target["name"])
            new_date = st.date_input("日付", value=datetime.strptime(target["date"], "%Y-%m-%d"))
            new_start = st.time_input("出勤時間", value=datetime.strptime(target["start"], "%H:%M").time())
            new_end = st.time_input("退勤時間", value=datetime.strptime(target["end"], "%H:%M").time())
            new_memo = st.text_input("メモ", value=target["memo"])

            if st.button("この行を編集して保存"):
                df.loc[row_index] = [
                    new_name,
                    new_date.strftime("%Y-%m-%d"),
                    new_start.strftime("%H:%M"),
                    new_end.strftime("%H:%M"),
                    new_memo
                ]
                df.to_csv("shift.csv", index=False)
                st.success("編集内容を保存しました！")
        else:
            st.info("編集できるシフトデータがありません")


    # -------------------------
    # ③ 削除
    # -------------------------
    with tabs[2]:
        st.subheader("③ シフト削除")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None and len(df) > 0:
            st.dataframe(df, use_container_width=True)

            del_index = st.number_input("削除する行番号（0〜）", min_value=0, max_value=len(df)-1, step=1)

            if st.button("この行を削除する"):
                df = df.drop(del_index).reset_index(drop=True)
                df.to_csv("shift.csv", index=False)
                st.success("削除しました！")
        else:
            st.info("削除できるシフトデータがありません")

    # -------------------------
    # ④ CSV ダウンロード
    # -------------------------
    with tabs[3]:
        st.subheader("④ CSV ダウンロード")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None:
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="CSV をダウンロード",
                data=csv,
                file_name="shift.csv",
                mime="text/csv"
            )

    # -------------------------
    # ⑤ カレンダー表示（全員のシフト）
    # -------------------------
    with tabs[4]:
        st.subheader("⑤ 全員のシフトをカレンダー表示")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None and len(df) > 0:
            df = df.dropna(subset=["name", "date", "start", "end"])  # 不正データ除外

            unique_names = df["name"].unique()
            colors = [
                "#ff9999", "#99ccff", "#99ff99", "#ffcc99",
                "#cc99ff", "#ff99cc", "#66cccc", "#cccc66"
            ]
            color_map = {name: colors[i % len(colors)] for i, name in enumerate(unique_names)}

            events_admin = []
            for _, row in df.iterrows():
                try:
                    events_admin.append({
                        "title": f"{row['start']}-{row['end']} {row['name']}",
                        "start": f"{row['date']}T{row['start']}:00",
                        "end": f"{row['date']}T{row['end']}:00",
                        "color": color_map[row["name"]]
                    })
                except:
                    continue  # 不正な行はスキップ

            cal_settings_admin = {
                "initialView": "dayGridMonth",
                "height": 600,
                "expandRows": True,
                "allDaySlot": False,
                "eventTimeFormat": {
                    "hour": "2-digit",
                    "minute": "2-digit",
                    "hour12": False
                },
                "displayEventTime": False
            }

            calendar(events=events_admin, options=cal_settings_admin)
        else:
            st.info("表示できるシフトデータがありません")

    # -------------------------
    # ⑥ 日別人数カウント
    # -------------------------
    with tabs[5]:
        st.subheader("⑥ 日別人数カウント")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None:
            count_df = df.groupby("date")["name"].count().reset_index()
            count_df.columns = ["日付", "人数"]
            st.dataframe(count_df, use_container_width=True)

    # -------------------------
    # ⑦ 月間勤務時間集計
    # -------------------------
    with tabs[6]:
        st.subheader("⑦ 月間勤務時間集計")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None:
            df["start_dt"] = pd.to_datetime(df["date"] + " " + df["start"])
            df["end_dt"] = pd.to_datetime(df["date"] + " " + df["end"])
            df["hours"] = (df["end_dt"] - df["start_dt"]).dt.total_seconds() / 3600

            summary = df.groupby("name").agg(
                出勤日数=("date", "count"),
                合計時間=("hours", "sum"),
                平均時間=("hours", "mean")
            ).reset_index()

            st.dataframe(summary, use_container_width=True)

    # -------------------------
    # ⑧ 時間帯別人数集計（修正済み）
    # -------------------------
    with tabs[7]:
        st.subheader("⑧ 時間帯別人数集計（例：18〜21時）")

        try:
            df = pd.read_csv("shift.csv")
        except:
            st.info("まだシフトデータがありません")
            df = None

        if df is not None and len(df) > 0:
            start_range = st.time_input("集計開始時間", time(18, 0))
            end_range = st.time_input("集計終了時間", time(21, 0))

            df["start_dt"] = pd.to_datetime(df["date"] + " " + df["start"])
            df["end_dt"] = pd.to_datetime(df["date"] + " " + df["end"])

            def overlaps(row):
                range_start = datetime.combine(datetime.strptime(row["date"], "%Y-%m-%d"), start_range)
                range_end = datetime.combine(datetime.strptime(row["date"], "%Y-%m-%d"), end_range)
                return not (row["end_dt"] <= range_start or row["start_dt"] >= range_end)

            df["overlap"] = df.apply(overlaps, axis=1)

            count_df = df[df["overlap"]].groupby("date")["name"].count().reset_index()
            count_df.columns = ["日付", "人数"]

            st.dataframe(count_df, use_container_width=True)
        else:
            st.info("集計できるシフトデータがありません")

            
    # -------------------------
    # ⑨ シフト初期化
    # -------------------------
    with tabs[8]:
        st.subheader("⑨ シフトデータの初期化")

        st.warning("⚠️ この操作はすべてのシフトデータを削除し、空のCSVファイルを再作成します。")

        # 初期化完了メッセージの表示
        if st.session_state.get("init_done", False):
            st.success("シフトデータを初期化しました！")
            st.session_state.init_done = False  # 一度表示したらリセット

        if st.button("⚠️ シフトデータを初期化する"):
            try:
                import os
                if os.path.exists("shift.csv"):
                    os.remove("shift.csv")
                empty_df = pd.DataFrame(columns=["name", "date", "start", "end", "memo"])
                empty_df.to_csv("shift.csv", index=False)
                st.session_state.init_done = True  # フラグを立てる
                st.rerun()
            except Exception as e:
                st.error(f"初期化中にエラーが発生しました: {e}")

    # ★ 管理者画面はここで終了
    st.stop()

# -------------------------
# 一般ユーザー画面（スマホ・PC切り替え対応）
# -------------------------
import streamlit as st
import pandas as pd
from datetime import date, time, timedelta
import jpholiday
from streamlit_calendar import calendar
import os

st.subheader("シフト入力")

# 🌿 表示モード選択
if "is_mobile" not in st.session_state:
    st.session_state.is_mobile = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

mode = st.radio("表示モードを選択", ["PCビュー", "スマホビュー"], horizontal=True)
st.session_state.is_mobile = (mode == "スマホビュー")

# 🌿 カラム切り替え
if st.session_state.is_mobile:
    col1 = st.container()
    col2 = None
else:
    col1, col2 = st.columns([1.7, 1])

# 🌿 編集モード切り替え
with col1:
    if st.button("🛠 編集モードを切り替え"):
        st.session_state.edit_mode = not st.session_state.edit_mode

# 🌿 カレンダー用イベント
events = []

# 🌿 入力フォーム関数
def render_shift_input(target_container):
    with target_container:
        if st.session_state.is_mobile:
            st.markdown("""
                <style>
                input[type="date"] {
                    pointer-events: none;
                    background-color: #f0f0f0;
                }
                </style>
            """, unsafe_allow_html=True)

        selected_date_input = st.date_input("日付を選択", value=None)

        if selected_date_input:
            st.session_state.selected_date = selected_date_input.strftime("%Y-%m-%d")
            st.success(f"選択した日付：{st.session_state.selected_date}")
            events.append({
                "start": st.session_state.selected_date,
                "display": "background",
                "color": "#b2f2bb"
            })
        else:
            st.info("日付を選択してください")

        st.write("シフト時間を入力")
        start = st.time_input("出勤時間", time(9, 0))
        end = st.time_input("退勤時間", time(18, 0))
        memo = st.text_input("メモ（任意）")

        if st.button("保存する"):
            if st.session_state.selected_date is None:
                st.error("日付を選択してください")
            else:
                df = pd.DataFrame([{
                    "name": st.session_state.username,
                    "date": st.session_state.selected_date,
                    "start": start.strftime("%H:%M"),
                    "end": end.strftime("%H:%M"),
                    "memo": memo
                }])

                try:
                    old = pd.read_csv("shift.csv")
                    df = pd.concat([old, df], ignore_index=True)
                except:
                    pass

                df.to_csv("shift.csv", index=False)
                st.success("保存しました！")
                st.rerun()

# 🌿 土日・祝日背景イベントの追加
today = date.today()
year = today.year
month = today.month

for add_month in [0, 1]:
    y = year
    m = month + add_month
    if m > 12:
        m -= 12
        y += 1

    first = date(y, m, 1)
    last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    holidays = jpholiday.month_holidays(y, m)
    holiday_dates = set([str(h[0]) for h in holidays])

    d = first
    while d <= last:
        if d.weekday() == 5:
            events.append({"start": str(d), "display": "background", "color": "#d0e7ff"})
        if d.weekday() == 6:
            events.append({"start": str(d), "display": "background", "color": "#ffd6d6"})
        if str(d) in holiday_dates:
            events.append({"start": str(d), "display": "background", "color": "#ffcccc"})
        d += timedelta(days=1)

# 🌿 シフト読み込みとイベント追加
try:
    df = pd.read_csv("shift.csv", dtype=str)
    df["memo"] = df["memo"].fillna("")
    user_shifts = df[df["name"] == st.session_state.username].reset_index(drop=True)

    for _, row in user_shifts.iterrows():
        events.append({
            "title": "",
            "start": f"{row['date']}T{row['start']}",
            "end": f"{row['date']}T{row['end']}",
            "color": "#a0c4ff"
        })
except FileNotFoundError:
    df = pd.DataFrame(columns=["name", "date", "start", "end", "memo"])
    user_shifts = df.copy()

# 🌿 入力フォーム or 編集モード表示
if not st.session_state.edit_mode:
    if st.session_state.is_mobile:
        render_shift_input(col1)
    elif col2:
        render_shift_input(col2)
else:
    with col1:
        st.markdown("### 📋 あなたのシフト一覧")
        st.dataframe(user_shifts, height=200)

        st.markdown("### ✅ 削除したいシフトにチェックを入れてください")

        selected_indices = []
        col_left, col_right = st.columns(2)

        for i, row in user_shifts.iterrows():
            label = f"{row['date']} {row['start']}〜{row['end']} {row['memo']}"
            target_col = col_left if i % 2 == 0 else col_right
            if target_col.checkbox(label, key=f"shift_{i}"):
                selected_indices.append(i)

        if selected_indices:
            if st.button("🗑️ チェックしたシフトを削除"):
                for i in selected_indices:
                    target = user_shifts.iloc[i]
                    match = (
                        (df["name"] == target["name"]) &
                        (df["date"] == target["date"]) &
                        (df["start"] == target["start"]) &
                        (df["end"] == target["end"]) &
                        (df["memo"].fillna("") == target["memo"])
                    )
                    match_indices = df[match].index
                    if not match_indices.empty:
                        df = df.drop(index=match_indices[0])

                df = df.reset_index(drop=True)
                df.to_csv("shift.csv", index=False)
                st.success("選択されたシフトを削除しました！")
                st.rerun()
        else:
            st.info("削除したいシフトにチェックを入れてください。")

# 🌿 カレンダー表示
with col1:
    st.markdown(
        """
        <style>
        .fc {
            max-width: 100% !important;
            width: 100% !important;
            aspect-ratio: auto !important;
            margin: 0 auto;
            padding-top: 0px !important;
        }
        .fc-header-toolbar {
            margin-top: -10px !important;
            margin-bottom: 0px !important;
        }
        .fc .fc-scrollgrid {
            width: 100% !important;
        }
        .fc-event-time, .fc-event-title {
            margin-left: 0px !important;
            padding-left: 0px !important;
            text-align: left !important;
            display: block !important;
            font-size: 12px !important;
            line-height: 1.2 !important;
        }
        .fc-event {
            overflow: visible !important;
        }
        .fc-daygrid-event-dot {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    cal_settings = {
        "initialView": "dayGridMonth",
        "height": 425,
        "expandRows": True,
        "allDaySlot": False,
        "eventTimeFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        },
        "displayEventTime": True
    }

    calendar(events=events, options=cal_settings)
