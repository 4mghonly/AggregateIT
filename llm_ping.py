from llm import preflight
ok,detail=preflight()
print("QWEN PREFLIGHT:", "OK" if ok else "FAIL", detail)
if not ok:
    raise SystemExit("No configured Qwen credential returned HTTP 200")
