import os, requests
KEY = os.environ.get("QWEN_API_KEY", "")
MODEL = os.environ.get("QWEN_MODEL") or "qwen3.8-flash"
CANDIDATES = [
    ("secret-as-is", (os.environ.get("QWEN_BASE_URL") or "").rstrip("/")),
    ("intl", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
    ("china", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
]
success = False
for name, base in CANDIDATES:
    if not base:
        continue
    try:
        r = requests.post(base + "/chat/completions",
            headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 16},
            timeout=30)
        print("ENDPOINT %s -> %s %s" % (name, r.status_code, r.text[:300].replace("\n", " ")))
        success = success or r.status_code == 200
    except Exception as e:
        print("ENDPOINT %s -> EXC %s" % (name, str(e)[:200]))

if not success:
    raise SystemExit("No Qwen endpoint returned HTTP 200")
