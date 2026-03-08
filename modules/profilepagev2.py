import streamlit as st
from PIL import Image
from modules.user import get_current_user, get_all_users
from modules.karitunagari import get_friends

def render():
    st.title("プロフィール画面")

    current_user = get_current_user()
    if not current_user:
        st.warning("ログインしてください")
        return

    # --- 初期ユーザー情報 ---
    if "users" not in st.session_state:
        st.session_state.users = {}

    # --- 全ユーザー一覧
    # を取得 --- ではなく、友達のみ
    friends = get_friends(current_user)
    all_usernames = [current_user] + friends  # 自分 + 友達

    # current_user が未登録なら追加（不要かも）
    # if current_user not in all_usernames:
    #     all_usernames.append(current_user)

    # --- ユーザー情報を初期化（未登録なら空プロフィールを作成） ---

    # --- ユーザー情報を初期化（未登録なら空プロフィールを作成） ---
    for username in all_usernames:
        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "handle": username,
                "bio": "",
                "image": None,
                "posts": []
            }

    # --- 表示対象ユーザーを選択 ---
    default_index = all_usernames.index(current_user)
    selected_user = st.selectbox("表示するユーザー", all_usernames, index=default_index)
    profile = st.session_state.users[selected_user]
    is_own_profile = (selected_user == current_user)

    # --- プロフィール設定（自分のみ） ---
    if is_own_profile:
        st.markdown("### プロフィール設定")
        uploaded_image = st.file_uploader("プロフィール画像をアップロード", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            profile["image"] = Image.open(uploaded_image)

        # ハンドルネームはユーザー名と一致（編集不可）
        profile["handle"] = current_user
        st.text(f"ハンドルネーム： {profile['handle']}")

        profile["bio"] = st.text_area("自己紹介", profile.get("bio", ""))

    # --- プロフィール表示（誰でも閲覧可能） ---
    st.markdown("### プロフィール")
    if profile.get("image"):
        st.image(profile["image"], width=150)
    else:
        st.text("プロフィール画像なし")

    st.subheader(selected_user)
    st.text(f"ハンドルネーム： {profile.get('handle', '')}")
    st.write(profile.get("bio", ""))

    st.write("---")

    # --- 投稿（自分のみ） ---
    if is_own_profile:
        st.markdown("### 投稿する")
        new_post = st.text_area("新しい投稿を入力", "")
        if st.button("投稿"):
            if new_post.strip():
                profile["posts"].insert(0, new_post)
                st.success("投稿しました！")
            else:
                st.warning("投稿内容が空です。")

    # --- 投稿表示（誰でも閲覧可能） ---
    st.markdown("### 最近の投稿")
    if profile.get("posts"):
        for post in profile["posts"]:
            st.write(f"💬 {post}")
    else:
        st.write("まだ投稿はありません。")