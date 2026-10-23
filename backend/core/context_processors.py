from urllib.parse import quote

from django.conf import settings

from .cart import Cart


def whatsapp_url(text):
    if not settings.WHATSAPP_NUMBER:
        return ""
    return f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(text)}"


def cart(request):
    return {
        "store_enabled": settings.STORE_ENABLED,
        "cart_count": Cart(request).count() if settings.STORE_ENABLED else 0,
        "whatsapp_url": whatsapp_url("Olá! Vim pelo site da Lertrix Edições."),
    }
