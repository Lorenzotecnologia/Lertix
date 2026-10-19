"""Gerador de Pix "copia e cola" (BR Code estático, padrão do Banco Central)."""

import io
import re
import unicodedata

import qrcode
import qrcode.image.svg


def _ascii_upper(text, limit):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Za-z0-9 ]", "", text).upper().strip()[:limit]


def _field(field_id, value):
    return f"{field_id}{len(value):02d}{value}"


def _crc16(payload):
    crc = 0xFFFF
    for byte in payload.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def build_pix_payload(key, name, city, amount, txid):
    txid = re.sub(r"[^A-Za-z0-9]", "", txid)[:25] or "***"
    account = _field("00", "br.gov.bcb.pix") + _field("01", key)
    payload = (
        _field("00", "01")
        + _field("26", account)
        + _field("52", "0000")
        + _field("53", "986")
        + _field("54", f"{amount:.2f}")
        + _field("58", "BR")
        + _field("59", _ascii_upper(name, 25))
        + _field("60", _ascii_upper(city, 15))
        + _field("62", _field("05", txid))
        + "6304"
    )
    return payload + _crc16(payload)


def qr_svg(payload):
    image = qrcode.make(
        payload, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2
    )
    buffer = io.BytesIO()
    image.save(buffer)
    return buffer.getvalue().decode()
