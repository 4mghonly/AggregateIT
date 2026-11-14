"""Explicitly configured OpenAI-compatible inference transport; never sends by default.

This is a held analytical probe, not publication authorization or evidence verification.
"""
from __future__ import annotations
from urllib.parse import urlsplit
import json

def make_http_caller(*,base_url,model,api_key,transport=None):
    if not api_key:return None
    url=urlsplit(base_url if isinstance(base_url,str) else "")
    if (url.scheme!="https" or not url.hostname or url.username or url.password
        or url.fragment or url.query or url.port not in (None,443)
        or not url.path.rstrip("/").endswith("/v1")
        or url.hostname in ("localhost","127.0.0.1","::1")):
        raise ValueError("invalid_model_endpoint")
    if not isinstance(model,str) or not 1<=len(model)<=160 or any(x in model for x in "\r\n"):
        raise ValueError("invalid_model_identifier")
    if not isinstance(api_key,str) or len(api_key)>4096 or any(x in api_key for x in "\r\n"):
        raise ValueError("invalid_model_credential")
    endpoint=base_url.rstrip("/")+"/chat/completions"
    def call(system,payload):
        if not isinstance(system,str) or not isinstance(payload,str) or len(payload)>12000:
            raise ValueError("invalid_model_payload")
        if transport is None:
            import requests
            send=requests.post
        else:send=transport
        response=send(endpoint,headers={"Authorization":"Bearer "+api_key,
            "Content-Type":"application/json"},json={"model":model,
            "messages":[{"role":"system","content":system},{"role":"user","content":payload}],
            "temperature":0,"max_tokens":1200,"response_format":{"type":"json_object"}},
            timeout=(7,35),allow_redirects=False)
        try:
            if response.status_code!=200:raise ValueError("model_http_failure")
            if len(response.content)>30000:raise ValueError("model_response_oversized")
            data=response.json()
            if not isinstance(data,dict) or not isinstance(data.get("choices"),list) or not data["choices"]:
                raise ValueError("invalid_model_envelope")
            choice=data["choices"][0]
            if choice.get("finish_reason") in ("length","content_filter"):
                raise ValueError("model_output_incomplete")
            content=choice.get("message",{}).get("content")
            if not isinstance(content,str) or not content.strip():
                raise ValueError("invalid_model_content")
            return content
        finally:
            response.close()
    return call
