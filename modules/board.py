import streamlit as st
import sqlite3
from modules.utils import now_str, sanitize_message
from modules.user import get_current_user
from streamlit_autorefresh import st_autorefresh

DB_PATH = "db/mebius.db"

# 定数化（設計意図の明示）
MAX_TITLE_LEN = 64
MAX_MESSAGE_LEN = 150

# 🧱 DB初期化（スレッド・メッセージ）
def init_board_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS board_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp TEXT,
            thread_id INTEGER
        )''')
        conn.commit()
    finally:
        conn.close()

# 📥 スレッド・メッセージ処理
def create_thread(title):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT INTO threads (title, created_at) VALUES (?, ?)", (title, now_str()))
        conn.commit()
    finally:
        conn.close()

def load_threads():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT id, title, created_at FROM threads ORDER BY id DESC")
        return c.fetchall()
    finally:
        conn.close()

def search_threads(keyword):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, title, created_at FROM threads WHERE title LIKE ? ORDER BY id DESC",
            (f"%{keyword}%",)
        )
        return c.fetchall()
    finally:
        conn.close()

def save_message(username, message, thread_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO board_messages (username, message, timestamp, thread_id) VALUES (?, ?, ?, ?)",
            (username, message, now_str(), thread_id)
        )
        conn.commit()
    finally:
        conn.close()

def load_messages(thread_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, message, timestamp FROM board_messages WHERE thread_id=? ORDER BY id DESC",
            (thread_id,)
        )
        return c.fetchall()
    finally:
        conn.close()

def delete_message(message_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("DELETE FROM board_messages WHERE id=?", (message_id,))
        conn.commit()
    finally:
        conn.close()

# 🖥 UI表示
def render():
    st_autorefresh(interval=3000, key="board_refresh")  # 3秒ごとに自動更新
    init_board_db()
    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.subheader("🧵 掲示板スレッド一覧")

    # 🔍 スレッド検索フォーム
    search_keyword = st.text_input("🔎 スレッド検索（タイトル）")
    if search_keyword:
        threads = search_threads(search_keyword)
        if not threads:
            st.info("該当するスレッドはありません")
    else:
        threads = load_threads()

    # スレッド作成フォーム
    with st.form(key="thread_form", clear_on_submit=True):
        new_title = st.text_input(f"新しいスレッド名（{MAX_TITLE_LEN}文字まで）", max_chars=MAX_TITLE_LEN)
        submitted = st.form_submit_button("スレッド作成")
        if submitted:
            title = sanitize_message(new_title, MAX_TITLE_LEN)
            if title:
                create_thread(title)
                st.success("スレッドを作成しました")
                st.rerun()
            else:
                st.warning("スレッド名を入力してください")

    st.markdown("---")

    # スレッド一覧表示
    for tid, title, created in threads:
        if st.button(f"{title}（{created} JST）", key=f"thread_{tid}"):
            st.session_state.thread_id = tid
            st.rerun()

    # スレッド選択後の表示
    if "thread_id" in st.session_state:
        st.subheader(f"🗨️ スレッド: {st.session_state.thread_id}")
        if st.button("← スレ一覧に戻る"):
            del st.session_state.thread_id
            st.rerun()

        messages = load_messages(st.session_state.thread_id)
        for mid, username, msg, ts in messages:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"[{ts} JST] **{username}**: {msg}")
            with col2:
                if username == user:
                    if st.button("🗑️", key=f"delete_{mid}"):
                        delete_message(mid)
                        st.rerun()

        # メッセージ送信欄
        msg = st.chat_input(f"メッセージ（{MAX_MESSAGE_LEN}文字まで）")
        if msg:
            msg = sanitize_message(msg, MAX_MESSAGE_LEN)
            save_message(user, msg, st.session_state.thread_id)
            st.rerun()

# メイン
if __name__ == "__main__":
    render()
