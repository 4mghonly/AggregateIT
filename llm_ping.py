from llm import preflight
ok,detail=preflight()
print("LLM PREFLIGHT:", "OK" if ok else "FAIL", detail)
if not ok:
    raise SystemExit("No configured LLM route returned HTTP 200")
