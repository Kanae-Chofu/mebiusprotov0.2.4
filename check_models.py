import os
from dotenv import load_dotenv
import requests

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Anthropic の公式ドキュメントから利用可能なモデルを確認
# https://docs.anthropic.com/en/docs/about/models/overview

# 既知のモデルリスト（2024年最新）
known_models = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229", 
    "claude-3-haiku-20240307",
    "claude-2.1",
    "claude-2",
    "claude-instant-1.2"
]

print("テストするモデル一覧：")
for model in known_models:
    print(f"  - {model}")

print("\n各モデルを試します...\n")

for model in known_models:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "hi"}]
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"✅ {model}: 成功！")
        else:
            error_msg = r.json().get("error", {}).get("message", "Unknown error")
            print(f"❌ {model}: {r.status_code} - {error_msg}")
    except Exception as e:
        print(f"❌ {model}: 例外 - {str(e)[:50]}")
