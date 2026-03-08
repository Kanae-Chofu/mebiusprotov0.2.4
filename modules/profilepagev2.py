import streamlit as st
from PIL import Image, ImageDraw
from modules.user import get_current_user, get_all_users
from modules.karitunagari import get_friends
from streamlit_autorefresh import st_autorefresh

def render():
    st_autorefresh(interval=3000, key="profile_refresh")  # 3秒ごとに自動更新
    st.title("プロフィール")

    current_user = get_current_user()
    if not current_user:
        st.warning("ログインしてください")
        return

    # --- 友達のみ表示 ---
    friends = get_friends(current_user)
    all_usernames = [current_user] + friends

    # --- ユーザー情報を初期化 ---
    if "users" not in st.session_state:
        st.session_state.users = {}

    for username in all_usernames:
        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "handle": username,
                "bio": "",
                "image": None,
                "posts": [],
                "header_image": None  # ヘッダー画像追加
            }

    # --- 表示対象ユーザーを選択 ---
    default_index = 0  # 自分をデフォルト
    selected_user = st.selectbox("ユーザー選択", all_usernames, index=default_index, key="user_select")
    profile = st.session_state.users[selected_user]
    is_own_profile = (selected_user == current_user)

    # --- Twitter風レイアウト ---
    # ヘッダー画像
    if profile.get("header_image"):
        st.image(profile["header_image"], use_column_width=True)
    else:
        # デフォルトヘッダー（グラデーション）
        header_img = Image.new('RGB', (800, 200), color=(0, 123, 255))
        draw = ImageDraw.Draw(header_img)
        draw.rectangle([0, 0, 800, 200], fill=(0, 123, 255))
        st.image(header_img, use_column_width=True)

    # プロフィール画像（丸く）
    col1, col2 = st.columns([1, 3])
    with col1:
        if profile.get("image"):
            # 丸くクリップ
            img = profile["image"].resize((100, 100))
            mask = Image.new('L', (100, 100), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 100, 100), fill=255)
            img.putalpha(mask)
            st.image(img, width=100)
        else:
            st.markdown('<div style="width:100px; height:100px; border-radius:50%; background-color:#ccc; display:flex; align-items:center; justify-content:center; color:#fff; font-size:24px;">👤</div>', unsafe_allow_html=True)

    with col2:
        st.subheader(selected_user)
        st.write(f"@{profile.get('handle', '')}")
        st.write(profile.get("bio", "自己紹介がありません。"))

    # --- タブ ---
    tab1, tab2 = st.tabs(["プロフィール", "投稿"])

    with tab1:
        if is_own_profile:
            st.markdown("### プロフィール編集")
            with st.expander("編集する"):
                uploaded_header = st.file_uploader("ヘッダー画像", type=["png", "jpg", "jpeg"], key="header_upload")
                if uploaded_header:
                    profile["header_image"] = Image.open(uploaded_header)

                uploaded_image = st.file_uploader("プロフィール画像", type=["png", "jpg", "jpeg"], key="profile_upload")
                if uploaded_image:
                    profile["image"] = Image.open(uploaded_image)

                profile["bio"] = st.text_area("自己紹介", profile.get("bio", ""), key="bio_edit")
                if st.button("保存", key="save_profile"):
                    st.success("プロフィールを更新しました！")
        else:
            st.write("このユーザーのプロフィールです。")

    with tab2:
        # --- 投稿 ---
        if is_own_profile:
            st.markdown("### 新しい投稿")
            new_post = st.text_area("何を考えていますか？", "", key="new_post")
            if st.button("投稿", key="post_btn"):
                if new_post.strip():
                    profile["posts"].insert(0, {"content": new_post, "timestamp": st.session_state.get("now", "今")})
                    st.success("投稿しました！")
                    st.rerun()
                else:
                    st.warning("投稿内容を入力してください。")

        # --- 投稿表示（タイムライン風） ---
        st.markdown("### タイムライン")
        if profile.get("posts"):
            for post in profile["posts"]:
                st.markdown(f"**{selected_user}**  {post.get('timestamp', '')}")
                st.write(post["content"])
                st.markdown("---")
        else:
            st.write("まだ投稿はありません。")