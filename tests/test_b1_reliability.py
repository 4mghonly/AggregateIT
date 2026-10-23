"""B1 reliability regressions. All HTTP, model, and delivery boundaries are mocked."""
import asyncio
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

import audit
import llm
from arabic_newsletter import editor
from v2_route_health import RouteJournal, outcome_for_http


class FakeResponse:
    def __init__(self, status, body=None):
        self.status_code = status
        self.text = "synthetic-error" if status != 200 else ""
        self.body = body or {}
    def json(self):
        return self.body
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("synthetic-http-error")


class RouteHealthTests(unittest.TestCase):
    def test_status_classes_and_bounded_non_sensitive_history(self):
        self.assertEqual(outcome_for_http(403), "auth_rejected")
        self.assertEqual(outcome_for_http(429), "transient_http")
        self.assertEqual(outcome_for_http(503), "transient_http")
        self.assertEqual(outcome_for_http(422), "permanent_http")
        journal = RouteJournal(max_entries=2)
        journal.record("arabic_chat", "primary", status=403)
        journal.record("arabic_chat", "fallback", outcome="invalid_content")
        journal.record("english_chat", "fallback", status=200)
        snapshot = journal.snapshot()
        self.assertEqual((snapshot["total_attempts"], snapshot["stored_attempts"], snapshot["dropped_detail"]), (3, 2, 1))
        self.assertNotIn("api_key", str(snapshot))
        with self.assertRaises(ValueError):
            journal.record("arabic_chat", "secret-route", status=200)

    def test_english_auth_error_fallback_is_sticky(self):
        good = FakeResponse(200, {"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]})
        with patch.multiple(llm, API_KEY="a", BASE_URL="https://example.test/v1", MODEL="model-a",
                            FALLBACK_API_KEY="b", FALLBACK_BASE_URL="https://fallback.test/v1",
                            FALLBACK_MODEL="model-b", _CONFIG_ERROR="", MAX_CALLS=5, _calls=0,
                            _force_fallback=False, ROUTE_JOURNAL=RouteJournal()):
            with patch.object(llm, "_request", side_effect=[FakeResponse(403), good, good]) as request:
                with patch.object(llm, "_load_json", return_value={}), patch.object(llm, "_save_ledger"), patch.object(llm, "_log_usage"):
                    self.assertEqual(llm.chat([{"role":"user","content":"first"}]), '{"ok":true}')
                    self.assertTrue(llm._force_fallback)
                    self.assertEqual(llm.chat([{"role":"user","content":"second"}]), '{"ok":true}')
                    self.assertEqual([x.args[7] for x in request.call_args_list], [False, True, True])
                    self.assertEqual(llm.ROUTE_JOURNAL.snapshot()["by_outcome"]["auth_rejected"], 1)

    def test_english_budget_limits_requests_even_when_fallback_exists(self):
        with patch.multiple(llm, API_KEY="a", BASE_URL="https://example.test/v1", MODEL="model-a",
                            FALLBACK_API_KEY="b", FALLBACK_BASE_URL="https://fallback.test/v1",
                            FALLBACK_MODEL="model-b", _CONFIG_ERROR="", MAX_CALLS=1, _calls=0,
                            _force_fallback=False, ROUTE_JOURNAL=RouteJournal()):
            with patch.object(llm, "_request", return_value=FakeResponse(403)) as request:
                with patch.object(llm, "_load_json", return_value={}):
                    with self.assertRaises(llm.BudgetExceeded):
                        llm.chat([{"role":"user","content":"limited"}])
                    self.assertEqual(request.call_count, 1)

    def test_arabic_compact_repair_switches_credentials_after_bad_primary(self):
        class MemoryState:
            def __init__(self): self.values = {}
            def get(self, key): return self.values.get(key)
            def put(self, key, value): self.values[key] = value
        class FakeRoot:
            def __truediv__(self, name): return self
            def read_text(self): return "{}"
        class FakeClient:
            last = None
            def __init__(self, *args, **kwargs):
                self.calls = 0
                self.switched = False
                FakeClient.last = self
            def chat(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise editor.EditorialError("Invalid or truncated model JSON after retry")
                return {"events":[]}
            def _switch_fallback(self):
                self.switched = True
                return True
        state = MemoryState()
        articles = [{"id":"syn-1","region":"gcc","language":"en","text":"synthetic example"}]
        with patch.object(editor, "Client", FakeClient), patch.object(editor, "ROOT", FakeRoot()), patch.object(editor, "_bounded_articles", return_value=articles):
            events, rejected = editor.synthesize(articles, state)
        self.assertEqual(events, [])
        self.assertEqual(rejected, [])
        self.assertEqual(FakeClient.last.calls, 2)
        self.assertTrue(FakeClient.last.switched)

    def test_one_reddit_exception_does_not_abort_source_audit(self):
        bad_social = types.SimpleNamespace(
            _reddit_official=Mock(side_effect=TimeoutError("synthetic credential-bearing URL")),
            _shift_get=Mock(return_value=[]),
        )
        audit.RESULTS.clear()
        with patch.dict(sys.modules, {"social": bad_social}):
            asyncio.run(audit.check_reddit(None, "synthetic", asyncio.Semaphore(1)))
        self.assertEqual(len(audit.RESULTS), 1)
        entry = audit.RESULTS.pop()
        self.assertFalse(entry["ok"])
        self.assertEqual(entry["err"], "TimeoutError")
        self.assertNotIn("credential-bearing", str(entry))


    def test_arabic_auth_403_fails_over_with_structured_diagnostics(self):
        class MemoryState:
            def __init__(self): self.data = {}
            def get(self, key): return self.data.get(key)
            def put(self, key, value): self.data[key] = value
        env = {
            "ARABIC_LLM_API_KEY":"first", "ARABIC_LLM_BASE_URL":"https://first.example/v1",
            "ARABIC_LLM_MODEL":"first-model", "ARABIC_LLM_FALLBACK_API_KEY":"second",
            "ARABIC_LLM_FALLBACK_BASE_URL":"https://second.example/v1",
            "ARABIC_LLM_FALLBACK_MODEL":"second-model",
        }
        good = FakeResponse(200, {"choices":[{"finish_reason":"stop",
                                              "message":{"content":'{"events":[]}'}}],
                                  "usage":{}})
        with patch.dict(os.environ, env, clear=True):
            client = editor.Client(MemoryState(), max_calls=3)
            with patch.object(editor.requests, "post", side_effect=[FakeResponse(403), good], create=True) as post:
                result = client.chat("JSON only", {"articles":[]}, use_cache=False)
        self.assertEqual(result, {"events":[]})
        self.assertEqual(post.call_count, 2)
        self.assertTrue(client.force_fallback_credential)
        self.assertEqual(client.route_journal.snapshot()["by_outcome"], {"auth_rejected":1, "success":1})
        self.assertNotIn("first", str(client.route_journal.snapshot()))

    def test_arabic_timeout_is_bounded_then_uses_fallback(self):
        class MemoryState:
            def __init__(self): self.data = {}
            def get(self, key): return self.data.get(key)
            def put(self, key, value): self.data[key] = value
        env = {
            "ARABIC_LLM_API_KEY":"first", "ARABIC_LLM_BASE_URL":"https://first.example/v1",
            "ARABIC_LLM_MODEL":"first-model", "ARABIC_LLM_FALLBACK_API_KEY":"second",
            "ARABIC_LLM_FALLBACK_BASE_URL":"https://second.example/v1",
            "ARABIC_LLM_FALLBACK_MODEL":"second-model",
        }
        good = FakeResponse(200, {"choices":[{"finish_reason":"stop","message":{"content":'{"events":[]}'}}],"usage":{}})
        with patch.dict(os.environ, env, clear=True):
            client = editor.Client(MemoryState(), max_calls=3)
            with patch.object(editor.requests, "post", side_effect=[editor.requests.Timeout(), editor.requests.Timeout(), good], create=True) as post:
                with patch.object(editor.time, "sleep"):
                    result = client.chat("JSON only", {"articles":[]}, use_cache=False)
        self.assertEqual(result, {"events":[]})
        self.assertEqual(post.call_count, 3)
        self.assertEqual(client.route_journal.snapshot()["by_outcome"]["transport_error"], 2)

    def test_arabic_malformed_primary_stays_for_compact_repair_before_failover(self):
        class MemoryState:
            def __init__(self): self.data = {}
            def get(self, key): return self.data.get(key)
            def put(self, key, value): self.data[key] = value
        env = {
            "ARABIC_LLM_API_KEY":"first", "ARABIC_LLM_BASE_URL":"https://first.example/v1",
            "ARABIC_LLM_MODEL":"first-model", "ARABIC_LLM_FALLBACK_API_KEY":"second",
            "ARABIC_LLM_FALLBACK_BASE_URL":"https://second.example/v1",
            "ARABIC_LLM_FALLBACK_MODEL":"second-model",
        }
        bad = FakeResponse(200, {"choices":[{"finish_reason":"length","message":{"content":"{}"}}],"usage":{}})
        with patch.dict(os.environ, env, clear=True):
            client = editor.Client(MemoryState(), max_calls=3)
            with patch.object(editor.requests, "post", side_effect=[bad, bad], create=True) as post:
                with patch.object(editor.time, "sleep"):
                    with self.assertRaisesRegex(editor.EditorialError, "Invalid or truncated"):
                        client.chat("JSON only", {"articles":[]}, use_cache=False)
        self.assertEqual(post.call_count, 2)
        self.assertFalse(client.force_fallback_credential)
        self.assertEqual(client.route_journal.snapshot()["by_outcome"]["invalid_content"], 2)


    def test_english_primary_recovers_after_fallback_fails(self):
        good = FakeResponse(200, {"choices":[{"finish_reason":"stop","message":{"content":"recovered"}}]})
        with patch.multiple(llm, API_KEY="a", BASE_URL="https://first.test/v1", MODEL="model-a",
                            FALLBACK_API_KEY="b", FALLBACK_BASE_URL="https://second.test/v1",
                            FALLBACK_MODEL="model-b", _CONFIG_ERROR="", MAX_CALLS=3, _calls=0,
                            _force_fallback=True, ROUTE_JOURNAL=RouteJournal()):
            with patch.object(llm, "_request", side_effect=[FakeResponse(403), good]) as request:
                with patch.object(llm, "_load_json", return_value={}), patch.object(llm, "_save_ledger"), patch.object(llm, "_log_usage"):
                    self.assertEqual(llm.chat([{"role":"user","content":"recover"}]), "recovered")
                    self.assertFalse(llm._force_fallback)
                    self.assertEqual([x.args[7] for x in request.call_args_list], [True, False])

    def test_arabic_analysis_fallback_is_marked_degraded(self):
        class MemoryState:
            def __init__(self): self.data = {}
            def get(self, key): return self.data.get(key)
            def put(self, key, value): self.data[key] = value
        class BrokenClient:
            def __init__(self, *args, **kwargs): pass
            def chat(self, *args, **kwargs): raise editor.EditorialError("synthetic timeout")
        state = MemoryState()
        events = [{"region":"gcc", "title_ar":"خبر تجريبي موثق",
                   "summary_ar":"ورد خبر تجريبي موثق.", "assessment_ar":"يحتمل استمرار المتابعة.",
                   "watch_ar":"مراقبة البيانات اللاحقة."}]
        with patch.object(editor, "Client", BrokenClient):
            analysis = editor.build_analysis(events, state)
        self.assertTrue(state.get("analysis_degraded"))
        self.assertTrue(analysis["situation_ar"])
        self.assertEqual(analysis["watch_ar"], ["مراقبة البيانات اللاحقة."])


if __name__ == "__main__":
    unittest.main()
