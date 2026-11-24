"""Small, offline observations made before writing the assertions."""
from io import BytesIO
from requests import Request

url = "https://example.test"
for data in ([], b"", {"n": [-7, 0, None]}, iter(())):
    req = Request("POST", url, data=data).prepare()
    # Iterators have machine-dependent repr, so report their kind instead.
    print("body", type(data).__name__, type(req.body).__name__, dict(req.headers))
req = Request("POST", url, cookies={"a": "1"}, data=BytesIO(b"abc")).prepare()
req.prepare_cookies({"b": "2"})
print("cookies", req.headers["Cookie"], req._cookies.get_dict())
clone = req.copy()
clone.register_hook("response", print)
print("shared hook", print in req.hooks["response"], "shared stream", clone.body is req.body)
for target in ("mailto:user@example.test", "https://bücher.example", ""):
    try:
        print("url", Request("GET", target, params={"q": 1}).prepare().url)
    except ValueError as exc:
        print("url error", type(exc).__name__)
