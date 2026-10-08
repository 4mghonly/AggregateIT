"""Strict OpenAI-compatible response decoding, without treating reasoning as output."""
import json
import re


def content_text(message):
    if not isinstance(message, dict):
        raise ValueError("message_object_required")
    content = message.get("content")
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    if isinstance(content, list):
        content = "".join(
            x if isinstance(x, str) else str(x.get("text") or x.get("content") or "")
            for x in content if isinstance(x, (str, dict))
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty_response_content")
    return content.strip()


def response_text(body):
    choice = body["choices"][0]
    if choice.get("finish_reason") == "length":
        raise ValueError("response_truncated")
    return content_text(choice["message"])


def json_object(text):
    """Accept a fenced JSON object, never partial JSON or reasoning-only content."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        obj = json.loads(text)
    except ValueError:
        decoder = json.JSONDecoder()
        obj = None
        for match in re.finditer(r"\{", text):
            try:
                candidate, _ = decoder.raw_decode(text[match.start():])
                if isinstance(candidate, dict):
                    obj = candidate
                    break
            except ValueError:
                continue
    if not isinstance(obj, dict):
        raise ValueError("json_object_required")
    return obj
