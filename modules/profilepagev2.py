import streamlit as st
from PIL import Image, ImageDraw
from modules.user import get_current_user, get_all_users
from modules.karitunagari import get_friends
from streamlit_autorefresh import st_autorefresh

import sqlite3
from datetime import datetime

# DBの初期化（テーブルがなければ作る）
def init_profile_db():
    conn = sqlite3.connect("db/mebius.db")
    c = conn.cursor()
    # プロフィール（自己紹介など）
    c.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
        username TEXT PRIMARY KEY,
        bio TEXT DEFAULT ''
    )''')
    # 投稿（タイムライン）
    c.execute('''CREATE TABLE IF NOT EXISTS user_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        content TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

# プロフィール取得
def get_profile_data(username):
    conn = sqlite3.connect("db/mebius.db")
    c = conn.cursor()
    c.execute("SELECT bio FROM user_profiles WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return {"bio": row[0] if row else "自己紹介がありません。"}

# 投稿取得
def get_db_posts(username):
    conn = sqlite3.connect("db/mebius.db")
    c = conn.cursor()
    c.execute("SELECT content, timestamp FROM user_posts WHERE username=? ORDER BY id DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return [{"content": r[0], "timestamp": r[1]} for r in rows]

def render():
    init_profile_db()  # DB準備
    st_autorefresh(interval=5000, key="profile_refresh") # 編集の邪魔にならないよう少し長めに
    st.title("プロフィール")

    current_user = get_current_user()
    if not current_user:
        st.warning("ログインしてください")
        return

    # 友達リスト取得
    friends = get_friends(current_user)
    all_usernames = [current_user] + friends

    # 表示対象ユーザーを選択
    selected_user = st.selectbox("ユーザー選択", all_usernames)
    
    # --- DBからデータをロード ---
    profile = get_profile_data(selected_user)
    posts = get_db_posts(selected_user)
    is_own_profile = (selected_user == current_user)

    # --- レイアウト表示（ヘッダー等は一旦デフォルト表示） ---
    header_img = Image.new('RGB', (800, 200), color=(0, 123, 255))
    st.image(header_img, use_column_width=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown('<div style="width:100px; height:100px; border-radius:50%; background-color:#ccc; display:flex; align-items:center; justify-content:center; color:#fff; font-size:24px;">👤</div>', unsafe_allow_html=True)
    with col2:
        st.subheader(selected_user)
        st.write(f"@{selected_user}")
        st.write(profile["bio"])

    tab1, tab2 = st.tabs(["プロフィール", "投稿"])

    with tab1:
        if is_own_profile:
            st.markdown("### プロフィール編集")
            with st.expander("編集する"):
                new_bio = st.text_area("自己紹介", profile["bio"])
                if st.button("保存"):
                    conn = sqlite3.connect("db/mebius.db")
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO user_profiles (username, bio) VALUES (?, ?)", (current_user, new_bio))
                    conn.commit()
                    conn.close()
                    st.success("保存したぞ！")
                    st.rerun()

    with tab2:
        if is_own_profile:
            st.markdown("### 新しい投稿")
            new_post_content = st.text_area("何を考えていますか？", key="post_input")
            if st.button("投稿"):
                if new_post_content.strip():
                    conn = sqlite3.connect("db/mebius.db")
                    c = conn.cursor()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO user_posts (username, content, timestamp) VALUES (?, ?, ?)", 
                              (current_user, new_post_content, now))
                    conn.commit()
                    conn.close()
                    st.success("投稿完了！")
                    st.rerun()

        # タイムライン表示
        st.markdown("### タイムライン")
        for post in posts:
            st.markdown(f"**{selected_user}** <span style='color:gray; font-size:0.8em;'>{post['timestamp']}</span>", unsafe_allow_html=True)
            st.write(post["content"])
            st.markdown("---")