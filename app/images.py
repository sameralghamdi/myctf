"""Minimal, dependency-free validation for user-uploaded profile photos.

Only PNG and JPEG are accepted, identified by their magic bytes (the client's
filename and Content-Type are ignored). Metadata that can leak private data
(EXIF with GPS position, XMP, IPTC, text chunks, comments) is stripped, and
dimensions are bounded so a stored image can't be a decompression bomb for
other players' browsers. The browser UI already re-encodes photos to a small
square JPEG; this is the server-side guarantee.
"""
from __future__ import annotations

import struct

MAX_BYTES = 512 * 1024
MAX_SIDE = 4096

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Chunks needed to render a PNG faithfully; everything else (tEXt, iTXt, zTXt,
# eXIf, tIME, private chunks…) is dropped.
PNG_KEEP = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"pHYs"}
# JPEG APPn segments to keep: APP0 (JFIF), APP2 (ICC colour profile), APP14 (Adobe colour transform).
JPEG_KEEP_APP = {0xE0, 0xE2, 0xEE}
JPEG_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


class ImageError(ValueError):
    pass


def _check_size(width: int, height: int) -> None:
    if not (0 < width <= MAX_SIDE and 0 < height <= MAX_SIDE):
        raise ImageError(f"Image must be at most {MAX_SIDE}×{MAX_SIDE} pixels.")


def _clean_png(data: bytes) -> bytes:
    out, pos, seen_ihdr = [PNG_SIGNATURE], len(PNG_SIGNATURE), False
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            raise ImageError("The PNG file is truncated.")
        if not seen_ihdr:
            if kind != b"IHDR" or length != 13:
                raise ImageError("Not a valid PNG file.")
            width, height = struct.unpack(">II", data[pos + 8:pos + 16])
            _check_size(width, height)
            seen_ihdr = True
        if kind in PNG_KEEP:
            out.append(data[pos:end])
        pos = end
        if kind == b"IEND":
            return b"".join(out)
    raise ImageError("The PNG file is truncated.")


def _clean_jpeg(data: bytes) -> bytes:
    out, pos, size_ok = [b"\xff\xd8"], 2, False
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise ImageError("Not a valid JPEG file.")
        marker = data[pos + 1]
        if marker == 0xFF:  # fill byte
            pos += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        end = pos + 2 + length
        if length < 2 or end > len(data):
            raise ImageError("The JPEG file is truncated.")
        if marker in JPEG_SOF:
            if length < 7:
                raise ImageError("Not a valid JPEG file.")
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            _check_size(width, height)
            size_ok = True
        if marker == 0xDA:  # start of scan: the rest is image data
            if not size_ok:
                raise ImageError("Not a valid JPEG file.")
            out.append(data[pos:])
            return b"".join(out)
        keep = not (0xE0 <= marker <= 0xEF or marker == 0xFE) or marker in JPEG_KEEP_APP
        if keep:
            out.append(data[pos:end])
        pos = end
    raise ImageError("The JPEG file is truncated.")


def sanitize_avatar(data: bytes) -> tuple[str, bytes]:
    """Return (mime type, cleaned bytes) or raise ImageError with a user-facing message."""
    if not data:
        raise ImageError("Choose an image to upload.")
    if len(data) > MAX_BYTES:
        raise ImageError("Image is too large (max 512 KB).")
    if data.startswith(PNG_SIGNATURE):
        return "image/png", _clean_png(data)
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", _clean_jpeg(data)
    raise ImageError("Only PNG or JPEG images are allowed.")
