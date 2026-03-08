import os
from dotenv import load_dotenv
import requests

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
print(f"CLAUDE_API_KEY starts with: {CLAUDE_API_KEY[:20] if CLAUDE_API_KEY else 'NOT FOUND'}")

if CLAUDE_API_KEY:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "test"}]
    }

    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")

    try:
        print("\nAPI リクエストを送信中...")
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"ステータスコード: {r.status_code}")
        print(f"レスポンス: {r.text}")
        if r.status_code == 200:
            data = r.json()
            print(f"成功: {data['content'][0]['text']}")
    except Exception as e:
        print(f"エラー: {e}")
else:
    print("CLAUDE_API_KEY が見つかりません")

