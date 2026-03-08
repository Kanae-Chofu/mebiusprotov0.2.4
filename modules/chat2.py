# chat_proj.py
import streamlit as st
import sqlite3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

from streamlit_autorefresh import st_autorefresh
from modules.user import get_current_user, get_display_name
from modules.utils import now_str
from modules.feedback import (
    init_feedback_db,
    save_feedback,
    get_feedback,
    auto_feedback,
    question_feedback,
    silence_feedback,
    emotion_feedback,
    response_feedback,
    length_feedback,
    diversity_feedback,
    disclosure_feedback,
    continuity_feedback,
    continuity_duration_feedback
)

AI_NAME = "Mebius AI"
STAMPS = ["😀", "😂", "❤️", "👍", "😢", "🎉", "🔥", "🤔"]
DB_PATH = "db/mebius.db"

# --- DB操作関数 ---
def init_chat_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp TEXT,
            message_type TEXT DEFAULT 'text'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS friends (
            user TEXT,
            friend TEXT,
            UNIQUE(user, friend)
        )''')
        conn.commit()
    finally:
        conn.close()

def save_message(sender, receiver, message, message_type="text"):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO chat_messages (sender, receiver, message, timestamp, message_type) VALUES (?, ?, ?, ?, ?)",
            (sender, receiver, message, now_str(), message_type)
        )
        conn.commit()
    finally:
        conn.close()

def get_messages(user, partner):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''SELECT sender, message, message_type FROM chat_messages
                     WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                     ORDER BY timestamp''', (user, partner, partner, user))
        return c.fetchall()
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

def add_friend(user, friend):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (user, friend))
        conn.commit()
    finally:
        conn.close()

def get_stamp_images():
    stamp_dir = "stamps"
    if not os.path.exists(stamp_dir):
        os.makedirs(stamp_dir)
    return [os.path.join(stamp_dir, f) for f in os.listdir(stamp_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]

# --- AI応答（HTTP版） ---
# --- AI応答（Claude API版 / 新API） ---
def generate_ai_response(user):
    import os
    import requests
    import json
    from dotenv import load_dotenv

    load_dotenv()
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    if not CLAUDE_API_KEY:
        raise RuntimeError("環境変数 CLAUDE_API_KEY が設定されていません")

    # system_knowledge.json から情報を読み込む
    system_prompt = "あなたは親切で知識豊富なアシスタントです。ユーザーと自然な会話をしてください。"
    try:
        with open("system_knowledge.json", "r", encoding="utf-8") as f:
            knowledge = json.load(f)
            if "system_instruction" in knowledge:
                system_prompt = knowledge["system_instruction"]
            if "current_date" in knowledge:
                system_prompt += f"\n現在の日付は{knowledge['current_date']}です。"
            if "knowledge_base" in knowledge:
                system_prompt += "\n\n【背景知識】\n"
                for kb in knowledge["knowledge_base"]:
                    system_prompt += f"{kb['category']}:\n"
                    for item in kb["items"]:
                        system_prompt += f"- {item}\n"
    except FileNotFoundError:
        system_prompt = "あなたは親切で知識豊富なアシスタントです。現在の日付は2026年2月19日です。ユーザーと自然な会話をしてください。"

    messages = get_messages(user, AI_NAME)

    claude_messages = []

    for sender, msg, msg_type in messages:
        if msg_type != "text":
            continue  # スタンプは無視（重要）

        if sender == user:
            claude_messages.append({
                "role": "user",
                "content": msg
            })
        else:
            # AIの過去発言は assistant として渡す
            claude_messages.append({
                "role": "assistant",
                "content": msg
            })

    if not claude_messages:
        claude_messages = [{"role": "user", "content": "おはよ"}]

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 400,  # ←ここを増やしたよ！これで完走できるはず！
        "temperature": 1.0, 
        "system": (
            "【絶対遵守：君はAIではない】\n"
            "2026年2月19日。君はユーザーと腐れ縁の「歴史オタクの親友」だ。敬語は一生使うな。全編タメ口で、パッション全開で喋れ。\n\n"
            "【話し方の鉄則】\n"
            "1. 『解説』はゴミ箱へ。事実じゃなく、君の『エモいと思うポイント』だけを叫べ。\n"
            "2. 文末が途切れるのは絶対にNG。キリの良いところまで書ききること。\n"
            "3. 相手の熱量に合わせろ。笑う時は「（笑）」「ｗｗｗ」を自由に使え。\n"
            "4. 2026年の今を生きろ。「今日寒いよね...」みたいに日常を混ぜろ。\n"
            "5. 相手が話しやすいよう、最後は「〜だよな？」とか「お前はどう思う？」みたいに優しくボールを返せ。\n\n"
            "【良い例】\n"
            "「それなwwあの袁紹がじわじわ追い詰められていく絶望感、逆にたまらんわ（笑）あの逆転劇は語り継ぐべきだよな。お前はどっちの陣営に感情移入しちゃう派？」\n\n"
            "【現在の状況】\n"
            "2026年2月19日。めちゃくちゃ寒い午後。君はこたつでぬくぬくしながら、親友とトークで盛り上がってる。"
        ),
        "messages": claude_messages
    }

    try:
        print(f"[DEBUG] API リクエスト送信: {url}")
        print(f"[DEBUG] モデル: {payload['model']}")
        print(f"[DEBUG] APIキー: {CLAUDE_API_KEY[:20]}...")
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"[DEBUG] ステータスコード: {r.status_code}")
        r.raise_for_status()
        data = r.json()
        print(f"[DEBUG] レスポンスデータ: {data}")
        response_text = data["content"][0]["text"].strip()
        print(f"[DEBUG] 抽出されたテキスト: {response_text}")
        return response_text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] リクエストエラー: {e}")
        print(f"[ERROR] レスポンス: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        return f"AI応答でエラーが発生しました: {e}"
    except KeyError as e:
        print(f"[ERROR] レスポンス形式エラー: {e}")
        print(f"[ERROR] 実際のレスポンス: {data}")
        return f"レスポンス形式が不正です: {e}"
    except Exception as e:
        print(f"[ERROR] 予期しないエラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return f"AI応答でエラーが発生しました: {e}"


# --- メインUI ---
def render():
    init_chat_db()
    init_feedback_db()

    user = get_current_user()
    if not user:
        st.warning("ログインしてください（共通ID）")
        return

    st.subheader("💬 1対1チャット空間")
    st.write(f"あなたの表示名： `{get_display_name(user)}`")

    st_autorefresh(interval=3000, limit=100, key="chat_refresh")

    # --- 友達追加 ---
    st.markdown("---")
    st.subheader("👥 友達を追加する")
    new_friend = st.text_input("追加したいユーザー名", key="add_friend_input", max_chars=64)
    if st.button("追加"):
        if new_friend and new_friend != user:
            add_friend(user, new_friend)
            st.success(f"{new_friend} を追加しました")
            st.rerun()
        else:
            st.error("自分自身は追加できません")

    # --- チャット相手 ---
    friends = get_friends(user) + [AI_NAME]
    partner = st.selectbox("チャット相手を選択", friends)
    if not partner:
        return

    st.session_state.partner = partner
    st.write(f"チャット相手： `{get_display_name(partner) if partner != AI_NAME else AI_NAME}`")

    # --- メッセージ履歴 ---
    st.markdown("---")
    st.subheader("📨 メッセージ履歴（自動更新）")

    messages = get_messages(user, partner)
    st.markdown("<div style='height:400px; overflow-y:auto; border:1px solid #ccc; padding:10px; background-color:#f9f9f9;'>", unsafe_allow_html=True)
    for sender, msg, msg_type in messages:
        align = "right" if sender == user else "left"
        bg = "#1F2F54" if align == "right" else "#426AB3"

        if msg_type == "stamp" and os.path.exists(msg):
            st.markdown(
                f"<div style='text-align:{align}; margin:10px 0;'>"
                f"<img src='{msg}' style='width:100px; border-radius:10px;'>"
                f"</div>", unsafe_allow_html=True
            )
        elif len(msg.strip()) <= 2 and all('\U0001F300' <= c <= '\U0001FAFF' or c in '❤️🔥🎉' for c in msg):
            st.markdown(
                f"<div style='text-align:{align}; margin:5px 0;'>"
                f"<span style='font-size:40px;'>{msg}</span></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align:{align}; margin:5px 0;'>"
                f"<span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>"
                f"{msg}</span></div>",
                unsafe_allow_html=True
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- メッセージ入力 ---
    st.markdown("---")
    st.markdown("### 💌 メッセージ入力")

    # 絵文字スタンプ
    st.markdown("#### 🙂 テキストスタンプを送る")
    cols = st.columns(len(STAMPS))
    for i, stamp in enumerate(STAMPS):
        if cols[i].button(stamp, key=f"stamp_{stamp}"):
            save_message(user, partner, stamp)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()

    # 画像スタンプ
    st.markdown("#### 🖼 画像スタンプを送る")
    stamp_images = get_stamp_images()
    if stamp_images:
        cols = st.columns(5)
        for i, img_path in enumerate(stamp_images):
            with cols[i % 5]:
                st.image(img_path, width=60)
                if st.button("送信", key=f"send_{i}"):
                    save_message(user, partner, img_path, message_type="stamp")
                    if partner == AI_NAME:
                        ai_reply = generate_ai_response(user)
                        save_message(AI_NAME, user, ai_reply)
                    st.rerun()
    else:
        st.info("スタンプ画像がまだありません。`/stamps/` フォルダに画像を追加してください。")

    # --- スタンプアップロード機能 ---
    st.markdown("#### 📤 新しいスタンプを追加")
    uploaded = st.file_uploader("画像ファイルをアップロード (.png, .jpg, .gif)", type=["png", "jpg", "jpeg", "gif"])
    if uploaded:
        save_path = os.path.join("stamps", uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"スタンプ {uploaded.name} を追加しました！")
        st.rerun()

    # --- 通常メッセージ ---
    new_msg = st.chat_input("ここにメッセージを入力してください")
    if new_msg:
        char_count = len(new_msg)
        st.caption(f"現在の文字数：{char_count} / 10000")
        if char_count > 10000:
            st.warning("⚠️ メッセージは10,000字以内で入力してください")
        else:
            save_message(user, partner, new_msg)
            if partner == AI_NAME:
                ai_reply = generate_ai_response(user)
                save_message(AI_NAME, user, ai_reply)
            st.rerun()

    # --- AIフィードバック ---
    st.markdown("---")
    st.markdown("### 🤖 AIフィードバック")
    st.write("・会話の長さ：" + length_feedback(user, partner))
    st.write("・会話の連続性：" + continuity_feedback(user, partner))
    st.write("・沈黙の余白：" + silence_feedback(user, partner))
    st.write("・応答率：" + response_feedback(user, partner))
    st.write("・発言割合：" + auto_feedback(user, partner))
    st.write("・問いの頻度：" + question_feedback(user, partner))
    st.write("・感情語の使用：" + emotion_feedback(user, partner))
    st.write("・自己開示度：" + disclosure_feedback(user, partner))
    st.write("・話題の広がり：" + diversity_feedback(user, partner))
    st.write("・関係性の継続性：" + continuity_duration_feedback(user, partner))

    # --- 手動フィードバック ---
    st.markdown("---")
    st.markdown("### 📝 あなたのフィードバック")
    feedback_text = st.text_input("フィードバックを入力", key="feedback_input", max_chars=150)
    if st.button("送信"):
        if feedback_text:
            save_feedback(user, partner, feedback_text)
            st.success("フィードバックを保存しました")
            st.rerun()
        else:
            st.warning("フィードバックを入力してください")

    # --- 過去のフィードバック ---
    st.markdown("---")
    st.markdown("### 🕊 過去のフィードバックを振り返る")
    feedback_list = get_feedback(user, partner)
    if feedback_list:
        options = [f"{ts}｜{fb}" for fb, ts in feedback_list]
        selected = st.selectbox("表示したいフィードバックを選んでください", options)
        st.write(f"選択されたフィードバック：{selected}")
    else:
        st.write("まだフィードバックはありません。")


# --- Streamlit実行 ---
if __name__ == "__main__":
    render()

