from email import policy
from email.parser import BytesParser
from io import BytesIO

import pytest
from requests import Request
from requests.exceptions import InvalidHeader, InvalidJSONError, InvalidURL, MissingSchema

URL = "https://example.test"

def prepare(method="POST", url=URL, **kwargs):
    return Request(method, url, **kwargs).prepare()


def test_query_order():
    p = prepare("get", b" https://example.test:8443/path?x=1",
                params=[("n", -7), ("n", 0), ("skip", None)])
    assert p.method == "GET"
    assert p.url == "https://example.test:8443/path?x=1&n=-7&n=0"


def test_idna_host():
    assert prepare("GET", "https://bücher.example").url == "https://xn--bcher-kva.example/"


@pytest.mark.parametrize("target,error", [("", MissingSchema), ("http://", InvalidURL)])
def test_invalid_url(target, error):
    with pytest.raises(error):
        prepare(url=target)


def test_form_repeated_values():
    p = prepare(data={"n": [-7, 0, None]})
    assert p.body == "n=-7&n=0"
    assert p.headers["Content-Length"] == "8"
    assert p.headers["Content-Type"] == "application/x-www-form-urlencoded"


def test_large_body():
    data = b"z" * 65536
    p = prepare(data=data)
    assert p.body == data
    assert p.headers["Content-Length"] == "65536"


@pytest.mark.parametrize("method,length", [("POST", "0"), ("HEAD", None)])
def test_empty_body(method, length):
    p = prepare(method, data=b"")
    assert p.body is None
    assert p.headers.get("Content-Length") == length


def test_json_custom_type():
    p = prepare(json={"n": 0}, headers={"Content-Type": "application/vnd.demo+json"})
    assert p.body == b'{"n": 0}'
    assert p.headers["Content-Type"] == "application/vnd.demo+json"


def test_multipart_fields():
    p = prepare(data={"n": "0"}, files={"f": ("a.txt", BytesIO(b"abc"), "text/plain")})
    # Parse the generated boundary rather than asserting its random value.
    prefix = ("Content-Type: " + p.headers["Content-Type"] + "\r\n\r\n").encode()
    msg = BytesParser(policy=policy.default).parsebytes(prefix + p.body)
    parts = list(msg.iter_parts())
    assert [v.get_param("name", header="Content-Disposition") for v in parts] == ["n", "f"]
    assert [v.get_payload(decode=True) for v in parts] == [b"0", b"abc"]
    assert parts[1].get_filename() == "a.txt"
    assert parts[1].get_content_type() == "text/plain"


def test_nan_error():
    with pytest.raises(InvalidJSONError) as caught:
        prepare(json={"v": float("nan")})
    assert caught.value.request.method == "POST"


def test_invalid_header_type():
    with pytest.raises(InvalidHeader):
        prepare(headers={"X-Count": 3})


def test_non_http_skips_query():
    # Characterization: query parameters are ignored by the non-HTTP shortcut.
    assert prepare("GET", "mailto:user@example.test", params={"q": 1}).url == "mailto:user@example.test"


def test_stream_offset():
    stream = BytesIO(b"abcdef")
    stream.seek(2)
    p = prepare(data=stream)
    assert p.body is stream
    assert p._body_position == stream.tell() == 2
    assert p.headers["Content-Length"] == "4"


def test_empty_iterator():
    p = prepare(data=iter(()))
    assert p.headers["Transfer-Encoding"] == "chunked"
    assert "Content-Length" not in p.headers
    assert list(p.body) == []


def test_stream_with_files():
    with pytest.raises(NotImplementedError, match="mutually exclusive"):
        prepare(data=iter([b"x"]), files={"f": ("a", b"x")})


def test_failed_tell():
    class Unpositioned(BytesIO):
        def tell(self):
            raise OSError("position unavailable")
    p = prepare(data=Unpositioned(b"abc"))
    assert p._body_position is not None and not isinstance(p._body_position, int)
    assert p.headers["Transfer-Encoding"] == "chunked"


def test_second_cookie_header():
    # Characterization: the new jar and the previously generated header diverge.
    p = prepare(cookies={"a": "1"})
    p.prepare_cookies({"b": "2"})
    assert p.headers["Cookie"] == "a=1"
    assert p._cookies.get_dict() == {"b": "2"}


def test_copy_shares_hooks():
    # Characterization: mutating the clone's hook list also changes the original.
    original = prepare(headers={"X-Tag": "first"})
    clone = original.copy()
    def callback(response, **kwargs):
        return response
    clone.register_hook("response", callback)
    clone.headers["X-Tag"] = "second"
    assert original.hooks["response"] == [callback]
    assert original.headers["X-Tag"] == "first"


def test_auth_tuple():
    p = prepare(auth=("a", "b"))
    assert p.headers["Authorization"] == "Basic YTpi"
