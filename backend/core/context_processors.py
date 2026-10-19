from urllib.parse import quote

from django.conf import settings

from .cart import Cart


def whatsapp_url(text):
    if not settings.WHATSAPP_NUMBER:
        return ""
    return f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(text)}"


def cart(request):
    return {
        "cart_count": Cart(request).count(),
        "whatsapp_url": whatsapp_url("Olá! Vim pelo site da Lertrix Edições."),
    }
