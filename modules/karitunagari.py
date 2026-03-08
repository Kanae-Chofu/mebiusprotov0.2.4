import streamlit as st
import sqlite3
import random
from modules.user import get_current_user, get_kari_id
from modules.utils import now_str
from streamlit_autorefresh import st_autorefresh

DB_PATH = "db/mebius.db"

# 話題カード
TOPIC_CARDS = {
    "猫": ["猫派？犬派？", "飼ってる猫の名前は？", "猫の仕草で好きなものは？"],
    "ゲーム": ["最近ハマってるゲームは？", "感動した瞬間は？", "推しキャラは？"],
    "旅行": ["最近行った場所は？", "旅先での思い出は？", "理想の旅って？"],
    "音楽": ["よく聴くジャンルは？", "好きなアーティストは？", "音楽で救われた瞬間ある？"],
    "映画": ["最近観た映画は？", "泣いた映画ある？", "推し俳優は？"],
    "本": ["好きな作家は？", "人生変えた一冊ある？", "読書ってどんな時にする？"],
    "カフェ": ["お気に入りのカフェある？", "コーヒー派？紅茶派？", "理想のカフェ空間って？"],
    "学校": ["得意だった科目は？", "部活何してた？", "学校での思い出ある？"],
    "仕事": ["今どんな仕事してる？", "やりがい感じる瞬間は？", "理想の働き方って？"],
    "推し活": ["推しは誰？", "推しのどこが好き？", "推しに救われたことある？"],
    "SNS": ["よく使うSNSは？", "SNSで嬉しかったことある？", "SNSとの距離感どうしてる？"],
    "料理": ["得意料理ある？", "最近作ったものは？", "食べる専門？作る派？"],
    "天気": ["雨の日どう過ごす？", "好きな季節は？", "天気で気分変わるタイプ？"],
    "ファッション": ["服選びのこだわりある？", "好きな色は？", "最近買った服ある？"],
    "趣味": ["最近の趣味は？", "昔ハマってたことある？", "趣味って人生に必要？"],
    "睡眠": ["寝るの得意？", "理想の睡眠時間は？", "寝る前にすることある？"],
    "朝": ["朝型？夜型？", "朝のルーティンある？", "朝ごはん食べる派？"],
    "夜": ["夜ってどんな気分？", "夜に聴きたい音楽ある？", "夜更かしするタイプ？"],
    "ペット": ["飼ってるペットいる？", "ペットとの思い出ある？", "理想のペットは？"],
    "アート": ["好きな画家いる？", "美術館行く？", "自分で描いたことある？"],
    "スポーツ": ["観る派？やる派？", "好きなスポーツは？", "運動得意？"],
    "言葉": ["好きな言葉ある？", "座右の銘ってある？", "言葉に救われたことある？"]
}

# DB初期化
def init_kari_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS kari_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            topic_theme TEXT,
            timestamp TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS friends (
            user TEXT,
            friend TEXT,
            UNIQUE(user, friend)
        )''')
        conn.commit()
    finally:
        conn.close()

# メッセージ保存・取得
def save_message(sender, receiver, message, theme=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT INTO kari_messages (sender, receiver, message, topic_theme, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (sender, receiver, message, theme, now_str()))
        conn.commit()
    finally:
        conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''SELECT sender, message FROM kari_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (user, partner, partner, user))
        return c.fetchall()
    finally:
        conn.close()

def get_shared_theme(user, partner):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''SELECT topic_theme FROM kari_messages
                     WHERE ((sender=? AND receiver=?) OR (sender=? AND receiver=?))
                     AND topic_theme IS NOT NULL
                     ORDER BY timestamp LIMIT 1''', (user, partner, partner, user))
        result = c.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def add_friend(user, friend):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (user, friend))
        c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (friend, user))
        conn.commit()
    finally:
        conn.close()

def get_friends(user):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT friend FROM friends WHERE user=?", (user,))
        return [row[0] for row in c.fetchall()]
    finally:
        conn.close()

def render():
    st_autorefresh(interval=3000, key="kari_refresh")  # 3秒ごとに自動更新
    init_kari_db()
    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    kari_id = get_kari_id(user)
    st.subheader("🌌 仮つながりスペース")
    st.write(f"あなたの仮ID： `{kari_id}`")

    partner = st.text_input("話したい相手の仮IDを入力", key="partner_input")
    if partner:
        st.session_state.partner = partner
        st.write(f"相手： `{partner}`")

        # 共有テーマの取得
        shared_theme = get_shared_theme(kari_id, partner)

        # テーマがある場合は話題カードを表示
        if shared_theme:
            card_index = st.session_state.get("card_index", 0)
            st.markdown(f"この会話のテーマ：**{shared_theme}**")
            st.markdown(f"話題カード：**{TOPIC_CARDS[shared_theme][card_index]}**")
            if st.button("次の話題カード"):
                st.session_state.card_index = (card_index + 1) % len(TOPIC_CARDS[shared_theme])
                st.rerun()
        else:
            # テーマを選ぶ
            choices = random.sample(list(TOPIC_CARDS.keys()), 2)
            chosen = st.radio("話したいテーマを選んでください", choices)
            if st.button("このテーマで話す"):
                st.session_state.shared_theme = chosen
                st.session_state.card_index = 0
                st.rerun()

        # メッセージ表示
        messages = get_messages(kari_id, partner)
        for sender, msg in messages:
            align = "right" if sender == kari_id else "left"
            bg = "#1F2F54" if align == "right" else "#426AB3"
            st.markdown(
                f"""<div style='text-align:{align}; margin:5px 0;'>
                <span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>
                {msg}
                </span></div>""", unsafe_allow_html=True
            )

        # メッセージ入力部分
        MAX_MESSAGE_LEN = 10000
        st.markdown("### ✏️ メッセージ入力（最大10,000字）")
        new_msg = st.chat_input("ここにメッセージを入力してください")
        if new_msg:
            char_count = len(new_msg)
            st.caption(f"現在の文字数：{char_count} / {MAX_MESSAGE_LEN}")
            if char_count > MAX_MESSAGE_LEN:
                st.warning("⚠️ メッセージは10,000字以内で入力してください")
            else:
                theme = shared_theme or st.session_state.get("shared_theme")
                save_message(kari_id, partner, new_msg, theme)
                # 送信後に画面を更新
                st.rerun()
