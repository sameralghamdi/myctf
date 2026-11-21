"""Profile photo upload: validation, metadata stripping, serving and removal."""
from __future__ import annotations

import io
import struct
import zlib

from conftest import auth_headers, register


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def png(width=2, height=2, text=b"") -> bytes:
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    parts = [b"\x89PNG\r\n\x1a\n", _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))]
    if text:
        parts.append(_chunk(b"tEXt", text))
    parts += [_chunk(b"IDAT", zlib.compress(raw)), _chunk(b"IEND", b"")]
    return b"".join(parts)


def jpeg_with_exif() -> bytes:
    seg = lambda marker, body: b"\xff" + bytes([marker]) + struct.pack(">H", len(body) + 2) + body
    return (b"\xff\xd8" + seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
            + seg(0xE1, b"Exif\x00\x00GPS-SECRET-LOCATION")
            + seg(0xC0, b"\x08\x00\x01\x00\x01\x01\x01\x11\x00")
            + seg(0xDA, b"\x01\x01\x00\x00\x3f\x00") + b"\x00\x00" + b"\xff\xd9")


def upload(client, token, data: bytes, name="me.png"):
    return client.post("/api/profile/avatar", headers=auth_headers(token),
                       data={"avatar": (io.BytesIO(data), name)}, content_type="multipart/form-data")


def test_upload_png_strips_text_and_serves_it(client):
    _, token = register(client, "photo1")
    r = upload(client, token, png(text=b"Comment\x00secret"))
    assert r.status_code == 200, r.get_data(as_text=True)
    url = r.get_json()["avatar_url"]
    assert url.startswith("/api/avatars/")
    me = client.get("/api/session", headers=auth_headers(token)).get_json()["user"]
    assert me["avatar_url"] == url
    img = client.get(url, headers=auth_headers(token))
    assert img.status_code == 200 and img.mimetype == "image/png"
    assert b"secret" not in img.data and img.data.startswith(b"\x89PNG")
    assert img.headers["X-Content-Type-Options"] == "nosniff"


def test_jpeg_exif_is_removed(client):
    _, token = register(client, "photo2")
    r = upload(client, token, jpeg_with_exif(), "me.jpg")
    assert r.status_code == 200
    img = client.get(r.get_json()["avatar_url"], headers=auth_headers(token))
    assert img.mimetype == "image/jpeg" and b"GPS-SECRET" not in img.data and b"JFIF" in img.data


def test_rejects_non_images_and_huge_dimensions(client):
    _, token = register(client, "photo3")
    assert upload(client, token, b"<svg onload=alert(1)>", "x.svg").status_code == 400
    assert upload(client, token, b"GIF89a....", "x.gif").status_code == 400
    assert upload(client, token, png(width=5000, height=1)).status_code == 400
    assert upload(client, token, png()[:40]).status_code == 400  # truncated


def test_delete_and_scoreboard_shows_photo(client):
    import base64, codecs, re
    from conftest import start_lab, submit_flag
    _, token = register(client, "photo4")
    upload(client, token, png())
    iid = start_lab(client, token, "encoding-decoding")
    page = client.get(f"/labs/{iid}/", headers=auth_headers(token)).get_data(as_text=True)
    blob = re.search(r'<pre id="blob">([^<]+)</pre>', page).group(1).strip()
    submit_flag(client, token, "encoding-decoding", codecs.encode(base64.b64decode(blob).decode(), "rot_13"))
    rows = client.get("/api/leaderboard", headers=auth_headers(token)).get_json()
    assert rows[0]["avatar_url"]
    feed = client.get("/api/leaderboard/insights", headers=auth_headers(token)).get_json()["feed"]
    assert feed[0]["avatar_url"] == rows[0]["avatar_url"]
    assert client.delete("/api/profile/avatar", headers=auth_headers(token)).status_code == 200
    assert client.get("/api/session", headers=auth_headers(token)).get_json()["user"]["avatar_url"] is None
    assert client.get(rows[0]["avatar_url"], headers=auth_headers(token)).status_code == 404


def test_avatar_requires_login(client):
    fresh = client.application.test_client()
    assert fresh.get("/api/avatars/1").status_code == 401
    assert fresh.post("/api/profile/avatar").status_code == 401
